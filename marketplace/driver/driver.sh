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
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  --parameters=*)
    parameters="${i#*=}"
    shift
    ;;
  --test_parameters=*)
    test_parameters="${i#*=}"
    shift
    ;;
  --marketplace_tools=*)
    marketplace_tools="${i#*=}"
    shift
    ;;
  --wait_timeout=*)
    wait_timeout="${i#*=}"
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$deployer" ]] && deployer="$APP_DEPLOYER_IMAGE"
[[ -z "$parameters" ]] && parameters="{}"
[[ -z "$marketplace_tools" ]] && echo "--marketplace_tools required" && exit 1
[[ -z "$wait_timeout" ]] && wait_timeout=300

# Getting the directory of the running script
DIR="$(realpath $(dirname $0))"
echo $DIR

# Extract the config schema from the deployer.
schema="$(docker run --entrypoint="/bin/bash" --rm "$deployer" -c 'cat /data/schema.yaml')"

# Parse the config schema for the keys associated with name and namespace.
name_key=$(echo "$schema" \
  | "$marketplace_tools/scripts/yaml2json" \
  | jq -r '.properties
             | to_entries
             | .[]
             | select(.value."x-google-marketplace".type == "NAME")
             | .key')
namespace_key=$(echo "$schema" \
  | "$marketplace_tools/scripts/yaml2json" \
  | jq -r '.properties
             | to_entries
             | .[]
             | select(.value."x-google-marketplace".type == "NAMESPACE")
             | .key')

# Extract the name from parameters and generate a namespace.
name=$(echo "$parameters" | jq -r --arg key "$name_key" '.[$key]')
namespace="apptest-$(uuidgen)"

# Update the NAMESPACE property in parameters with the generated value.
parameters=$(echo "$parameters" \
  | jq \
      --arg namespace_key "$namespace_key" \
      --arg namespace "$namespace" \
      '.[$namespace_key] = $namespace')

echo "INFO Creates namespace \"$namespace\""
kubectl create namespace "$namespace"

function delete_namespace() {
  echo "INFO Collecting events for namespace \"$namespace\""
  kubectl get events --namespace=$namespace || echo "ERROR Failed to get events for namespace $namespace"

  if [[ ! -z $deployer_name ]]; then
    echo "INFO Collecting logs for deployer"
    kubectl logs "jobs/$deployer_name" --namespace="$namespace" || echo "ERROR Failed to get logs for deployer $deployer_name"
  fi
  
  echo "INFO Deleting namespace \"$namespace\""
  kubectl delete namespace "$namespace"
}

function clean_and_exit() {
  message=$1
  [[ -z "$message" ]] || echo "$message"

  delete_namespace
  exit 1
}

echo "INFO Creates the Application CRD in the namespace"
kubectl apply -f "$marketplace_tools/crd/app-crd.yaml"

echo "INFO Parameters: $parameters"

echo "INFO Initializes the deployer container which will deploy all the application components"
$marketplace_tools/scripts/start_test.sh \
  --deployer="$deployer" \
  --parameters="$parameters" \
  --test_parameters="$test_parameters" \
  --marketplace_tools="$marketplace_tools" \
  || clean_and_exit "ERROR Failed to start deployer"

echo "INFO wait for the deployer to succeed"
deployer_name="${name}-deployer"

start_time="$(date +%s)"
poll_interval=4
while true; do
  deployer_status=$(kubectl get "jobs/$deployer_name" --namespace="$namespace" -o=json | jq '.status' || echo "{}")
  failure=$(echo $deployer_status | jq '.failed')
  if [[ "$failure" -gt "0" ]]; then
    clean_and_exit "ERROR Deployer failed"
  fi

  success=$(echo $deployer_status | jq '.succeeded')
  if [[ "$success" -gt "0" ]]; then
    echo "INFO Deployer job succeeded"
    break
  fi

  elapsed_time=$(( $(date +%s) - $start_time ))
  echo -ne "Elapsed ${elapsed_time}s\r"
  if [[ "$elapsed_time" -gt "$wait_timeout" ]]; then
    clean_and_exit "ERROR Deployer job timeout"
  fi

  sleep "$poll_interval"
done

# Get the logs from the deployer before deleting the application. Set deployer name to empty so clean up doesn't try to get its logs again.
kubectl logs "jobs/$deployer_name" --namespace="$namespace" || echo "ERROR Failed to get logs for deployer $deployer_name"
deployer_name=""

echo "INFO Stop the application"
$marketplace_tools/scripts/stop.sh \
  --name="$name" \
  --namespace="$namespace" \
  || clean_and_exit "ERROR Failed to stop application"

deletion_timeout=60
echo "INFO Wait for the applications to be deleted"
timeout --foreground $deletion_timeout "$DIR/wait_for_deletion.sh" "$namespace" applications \
  || clean_and_exit "ERROR Some applications where not deleted"

echo "INFO Wait for standard resources were deleted."
timeout --foreground $deletion_timeout "$DIR/wait_for_deletion.sh" "$namespace" all \
  || clean_and_exit "ERROR Some resources where not deleted"

echo "INFO Wait for service accounts to be deleted."
timeout --foreground $deletion_timeout "$DIR/wait_for_deletion.sh" "$namespace" serviceaccounts,roles,rolebindings \
  || clean_and_exit "ERROR Some service accounts or roles where not deleted"

delete_namespace
