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

set -eo pipefail

for i in "$@"
do
case $i in
  --marketplace_tools=*)
    marketplace_tools="${i#*=}"
    shift
    ;;
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  --parameters=*)
    parameters="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$marketplace_tools" ]] && >&2 echo "--marketplace_tools required" && exit 1
[[ -z "$deployer" ]] && >&2 echo "--deployer required" && exit 1
[[ -z "$parameters" ]] && >&2 echo "--parameters required" && exit 1

# Unpack the deployer schema.
schema="$("$marketplace_tools/scripts/extract_deployer_config_schema.sh" \
  --deployer="$deployer")"

# Parse the config schema for the key associated with namespace.
namespace_key=$("$marketplace_tools/marketplace/deployer_util/extract_schema_key.py" \
    --schema_file=<(echo "$schema") \
    --type=NAMESPACE)

# Extract the namespace from parameters.
namespace=$(echo "$parameters" \
  | jq --raw-output --arg key "$namespace_key" '.[$key]')
export namespace

function print_bar() {
  character="$1"
  yes "$character" | tr -d '\n' | head -c$(tput cols)
}
export -f print_bar

function watch_function() {
  # TODO(trironkk): Extract printing and then running a command into a function.
  print_bar =
  echo "Application resources in the following namespace: \"$namespace\""
  echo "$ kubectl get applications --namespace=\"$namespace\" --show-kind"
  print_bar -
  echo -e "\n\n"
  kubectl get applications \
      --namespace="$namespace" \
      --show-kind

  echo -e "\n"
  print_bar =
  echo "Standard resources in the following namespace: \"$namespace\""
  echo "$ kubectl get all --namespace=\"$namespace\" --show-kind"
  print_bar -
  echo -e "\n\n"
  kubectl get all \
      --namespace="$namespace" \
      --show-kind

  echo -e "\n"
  print_bar =
  echo "Service accounts and roles in the following namespace: \"$namespace\""
  echo "$ kubectl get serviceaccounts,roles,rolebindings,PersistentVolumeClaims,configmap --namespace=\"$namespace\" --show-kind"
  print_bar -
  echo -e "\n\n"
  kubectl get serviceaccounts,roles,rolebindings,PersistentVolumeClaims,configmap \
      --namespace="$namespace" \
      --show-kind

  echo -e "\n"
  print_bar =
  echo "Events with the following label: app=\"$NAME\""
  echo "$ kubectl get events --namespace="$namespace" --selector="app=$NAME" \\
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'"
  print_bar -
  echo -e "\n\n"
  kubectl get events --namespace="$namespace" \
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'
}
export -f watch_function

watch --interval 1 --no-title --exec bash -c watch_function
