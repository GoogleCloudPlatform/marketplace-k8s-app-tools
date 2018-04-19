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

for i in "$@"
do
case $i in
  --application_uid=*)
    application_uid="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "application_uid" ]] && echo "application_uid required" && exit 1
[[ -z "APP_INSTANCE_NAME" ]] && echo "APP_INSTANCE_NAME not defined" && exit 1
[[ -z "NAMESPACE" ]] && echo "NAMESPACE not defined" && exit 1

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
                 uid: $application_uid" || true   
done