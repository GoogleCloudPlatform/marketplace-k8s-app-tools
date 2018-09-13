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
  --name=*)
    name="${i#*=}"
    shift
    ;;
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$name" ]] && >&2 echo "--name required" && exit 1
[[ -z "$namespace" ]] && >&2 echo "--namespace required" && exit 1

application_uid="$(kubectl get "applications/$name" \
    --namespace="$namespace" \
    --output=jsonpath='{.metadata.uid}')"
application_api_version="$(kubectl get "applications/$name" \
    --namespace="$namespace" \
    --output=jsonpath='{.apiVersion}')"
component_kinds="$(kubectl get "applications/$name" \
    --namespace="$namespace" \
    --output=yaml \
  | yaml2json \
  | jq -r '.spec.componentKinds[] 
             | [.group, .kind]
             | @csv' \
  | tr -d '"' \
  | sed 's/,/ /')"


# TODO(trironkk): Add Application labels.

manifests_directory="$(mktemp -d)"
echo "$component_kinds" | while read group kind; do
  kubectl get "$kind" \
      --namespace="$namespace" \
      --selector="heritage=Tiller,release=$name" \
      --output=yaml \
    | yaml2json \
    | jq '.items[]
            | {
                apiVersion: .apiVersion,
                kind: .kind,
                metadata: .metadata 
              }
            | del(.metadata.creationTimestamp)
            | .metadata.ownerReferences +=
              [
                {
                  apiVersion: $application_api_version,
                  kind: "Application",
                  name: $name,
                  uid: $application_uid,
                  blockOwnerDeletion: true
                }
              ]
            | .metadata.labels["app.kubernetes.io/name"] = $name
            | .metadata.labels["app.kubernetes.io/namespace"] = $namespace
         ' \
      --arg name "$name" \
      --arg namespace "$namespace" \
      --arg application_uid "$application_uid" \
      --arg application_api_version "$application_api_version" \
  > "$manifests_directory/$kind.json"
  echo
done

find "$manifests_directory" -type f -size 0 -delete

if [[ ! -z "$(ls -A "$manifests_directory")" ]]; then
	cat "$manifests_directory"/*
  kubectl apply -f "$manifests_directory"
fi
