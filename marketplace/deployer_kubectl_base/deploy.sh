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

set -e
set -o pipefail
set -x

# Assert existence of required environment variables.
[[ -v "APP_INSTANCE_NAME" ]] || exit 1
[[ -v "NAMESPACE" ]] || exit 1

kubectl patch "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --type=merge \
  --patch "metadata:
             annotations:
               kubernetes-engine.cloud.google.com/application-deploy-status: Assembly"

# Assign owner references to the existing kubernates resources tagged with the application name
APPLICATION_UID=$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')

top_level_kinds=$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=json \
  | jq -r '.spec.componentKinds[] | .kind')  

top_level_resources=() 
for kind in ${top_level_kinds[@]}; do  
  top_level_resources+=($(kubectl get "$kind" \
    --selector app.kubernetes.io/name="$APP_INSTANCE_NAME" \
    --output=json \
    | jq -r '.items[] | [.kind, .metadata.name] | join("/")')) 
done

for resource in ${top_level_resources[@]}; do 
  kubectl patch "$resource" \
    --namespace="$NAMESPACE" \
    --type=merge \
    --patch="metadata: 
               ownerReferences:  
               - apiVersion: extensions/v1beta1  
                 blockOwnerDeletion: true  
                 controller: true  
                 kind: Application 
                 name: $APP_INSTANCE_NAME  
                 uid: $APPLICATION_UID" || true   
done

# Perform environment variable expansions.
# Note: We list out all environment variables and explicitly pass them to
# envsubst to avoid expanding templated variables that were not defined
# in this container.
environment_variables="$(printenv \
  | sed 's/=.*$//' \
  | sed 's/^/$/' \
  | paste -d' ' -s)"

data_dir="/data"
manifest_dir="$data_dir/manifest-expanded"
mkdir "$manifest_dir"

# Replace the environment variables placeholders from the manifest templates
for manifest_template_file in "$data_dir"/manifest/*; do
  manifest_file=$(basename "$manifest_template_file" | sed 's/.template$//')
  
  cat "$manifest_template_file" \
    | envsubst "$environment_variables" \
    > "$manifest_dir/$manifest_file" 
done

# Set Application to own all resources defined in its component kinds.
# by inserting ownerReference in manifest before applying.''
resources_yaml="$data_dir/resources.yaml"
python /bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$APPLICATION_UID" \
  --manifests "$manifest_dir" \
  --dest "$resources_yaml"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="$resources_yaml"

kubectl patch "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --type=merge \
  --patch "metadata:
             annotations:
               kubernetes-engine.cloud.google.com/application-deploy-status: Assembled"
