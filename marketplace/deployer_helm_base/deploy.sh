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

datadir="/data"
manifestdir="$datadir/manifest-expanded"
mkdir $manifestdir

# Expand the chart template.
for chart in /data/chart/*; do
  chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//').yaml
  helm template "$chart" \
        --name="$APP_INSTANCE_NAME" \
        --namespace="$NAMESPACE" \
    > "$manifestdir/$chart_manifest_file"
done

# Set Application to own all resources defined in its component kinds.
# by inserting ownerReference in manifest before applying.
APPLICATION_UID="$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')"

resourcesyaml="$datadir/resources.yaml"
python /bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$APPLICATION_UID" \
  --manifests "$manifestdir" \
  --dest "$resourcesyaml"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename=$resourcesyaml
