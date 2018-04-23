#!/bin/bash
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -eox pipefail

# Assert existence of required environment variables.
[[ -v "APP_INSTANCE_NAME" ]] || exit 1
[[ -v "NAMESPACE" ]] || exit 1

# Perform environment variable expansions.
# Note: We list out all environment variables and explicitly pass them to
# envsubst to avoid expanding templated variables that were not defined
# by the config map.
# Note: We can deserialize this from a mounted volume, rather than
# fetching the config map independently.
environment_variables="$(kubectl get "configmap/$APP_INSTANCE_NAME-deployer-config" \
    --namespace="$NAMESPACE" \
    --output=json \
  | jq -r '.data | keys | @csv' \
  | tr -d '"' \
  | sed 's/^/$/' \
  | sed 's/,/,$/g')"

data_dir="/data"
manifest_dir="$data_dir/manifest-expanded"
mkdir "$manifest_dir"

# Expand the chart template.
for chart in "$data_dir"/chart/*; do
  # TODO(trironkk): Construct values.yaml directly from ConfigMap, rather than
  # stitching into values.yaml.template first.
  tar -xf "$chart" "chart/values.yaml.template"
  cat "chart/values.yaml.template" \
    | envsubst "$environment_variables" \
    > "values.yaml"
  chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//').yaml
  helm template "$chart" \
        --name="$APP_INSTANCE_NAME" \
        --namespace="$NAMESPACE" \
        --values="values.yaml" \
    > "$manifest_dir/$chart_manifest_file"

  rm "chart/values.yaml.template" "values.yaml"
done

# Fetch Application resource UID.
APPLICATION_UID="$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')"

# Set Application to own all resources defined in its component kinds.
# by inserting ownerReference in manifest before applying.
resources_yaml="$data_dir/resources.yaml"
python /bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$APPLICATION_UID" \
  --manifests "$manifest_dir" \
  --dest "$resources_yaml"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="$resources_yaml"

# Update Application resource with application-deploy-status.
kubectl patch "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --type=merge \
  --patch "metadata:
             annotations:
               kubernetes-engine.cloud.google.com/application-deploy-status: Succeeded"

# Clean up IAM resources.
kubectl delete --namespace="$NAMESPACE" --filename=- <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: "${APP_INSTANCE_NAME}-deployer-sa"
  namespace: "${NAMESPACE}"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: "${APP_INSTANCE_NAME}-deployer-rb"
  namespace: "${NAMESPACE}"
EOF
