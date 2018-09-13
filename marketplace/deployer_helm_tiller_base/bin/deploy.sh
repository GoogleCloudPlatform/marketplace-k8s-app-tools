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

# This is the entry point for the production deployment

# If any command returns with non-zero exit code, set -e will cause the script
# to exit. Prior to exit, set App assembly status to "Failed".
handle_failure() {
  code=$?
  if [[ -z "$NAME" ]] || [[ -z "$NAMESPACE" ]]; then
    # /bin/expand_config.py might have failed.
    # We fall back to the unexpanded params to get the name and namespace.
    NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}' \
            --values_file /data/values.yaml --values_dir /data/values)"
    NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}' \
                 --values_file /data/values.yaml --values_dir /data/values)"
    export NAME
    export NAMESPACE
  fi
  patch_assembly_phase.sh --status="Failed"
  exit $code
}
trap "handle_failure" EXIT

/bin/expand_config.py
NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"
export NAME
export NAMESPACE

echo "Deploying application \"$NAME\""

app_uid=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')
app_api_version=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.apiVersion}')

for chart in /data/chart/*; do
  # Expand and apply the template for the Application resource.
  # Note: This must be done out-of-band because the Application resource
  # is created before the deployer is invoked, but helm does not handle
  # pre-existing resources.
  helm template \
      --name="$NAME" \
      --namespace="$NAMESPACE" \
      --set "template_mode=true" \
      --values=<(print_config.py --output=yaml) \
      "$chart" \
    | yaml2json \
    | jq 'select( .kind == "Application" )' \
    | kubectl apply -f -

  # Install the chart.
  # Note: This does not assume that tiller is installed in the cluster;
  # it runs a local tiller process to perform template expansion and
  # hook processing.
  # Note: The local tiller process is configured with --storage=secret,
  # which is recommended but not default behavior.
  helm tiller run "$NAMESPACE" -- \
    helm install \
        --name="$NAME" \
        --namespace="$NAMESPACE" \
        --values=<(print_config.py --output=yaml) \
        "$chart"

  # Establish an ownerReference back to the Application resource, so that
  # the helm release will be cleaned up when the Application is deleted.
  # Note: This is fragile, as any time that tiller updates the release
  # it will remove the ownerReference. Also, any future Secret resources
  # created by tiller will not have this ownerReference established.
  kubectl get secrets \
      --namespace="$NAMESPACE" \
      --selector="OWNER=TILLER,NAME=$NAME" \
      --output=yaml \
    | yaml2json \
    | jq '.items[]
            | {
                apiVersion: .apiVersion,
                kind: .kind,
                metadata: .metadata
              }
            | del(.metadata.creationTimestamp)
            | del(.metadata.resourceVersion)
            | .metadata.ownerReferences +=
              [
                {
                  apiVersion: $app_api_version,
                  kind: "Application",
                  name: $name,
                  uid: $app_uid,
                  blockOwnerDeletion: true
                }
              ]
         ' \
      --arg name "$NAME" \
      --arg namespace "$namespace" \
      --arg app_uid "$app_uid" \
      --arg app_api_version "$app_api_version" \
    | kubectl apply -f -
done

patch_assembly_phase.sh --status="Success"

clean_iam_resources.sh

trap - EXIT
