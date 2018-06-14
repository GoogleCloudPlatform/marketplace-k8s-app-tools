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
[[ -z "$wait_timeout" ]] && wait_timeout=600

# Getting the directory of the running script
DIR="$(realpath $(dirname $0))"
echo $DIR

namespace_key="$(docker run --entrypoint=/bin/extract_schema_key.py --rm "$deployer" --type NAMESPACE)"
NAME="$(echo "$parameters" \
    | docker run -i --entrypoint=/bin/print_config.py --rm "$deployer" \
    --values_file=- --param '{"x-google-marketplace": {"type": "NAME"}}')"

export NAMESPACE="apptest-$(uuidgen)"
export NAME

kubectl version

echo "INFO Creates namespace \"$NAMESPACE\""
kubectl create namespace "$NAMESPACE"

function delete_namespace() {
  echo "INFO Collecting events for namespace \"$NAMESPACE\""
  kubectl get events --namespace=$NAMESPACE || echo "ERROR Failed to get events for namespace $NAMESPACE"

  if [[ ! -z $deployer_name ]]; then
    echo "INFO Collecting logs for deployer"
    kubectl logs "jobs/$deployer_name" --namespace="$NAMESPACE" || echo "ERROR Failed to get logs for deployer $deployer_name"
  fi

  echo "INFO Deleting namespace \"$NAMESPACE\""
  kubectl delete namespace $NAMESPACE
}

function clean_and_exit() {
  message=$1
  [[ -z "$message" ]] || echo "$message"

  delete_namespace
  exit 1
}

echo "INFO Creates the Application CRD in the namespace"
kubectl apply -f "$marketplace_tools/crd/app-crd.yaml"

parameters=$(echo "$parameters" \
  | jq \
    --arg namespace_key "$namespace_key" \
    --arg namespace "$NAMESPACE" \
    '.[$namespace_key] = $namespace')

echo "INFO Parameters: $parameters"

echo "INFO Initializes the deployer container which will deploy all the application components"
$marketplace_tools/scripts/start.sh \
  --name="$NAME" \
  --namespace="$NAMESPACE" \
  --deployer="$deployer" \
  --parameters="$parameters" \
  --entrypoint='/bin/deploy_with_tests.sh' \
  || clean_and_exit "ERROR Failed to start deployer"

echo "INFO wait for the deployer to succeed"
deployer_name="${NAME}-deployer"

start_time=$(date +%s)
poll_interval=4
while true; do
  deployer_status=$(kubectl get "jobs/$deployer_name" --namespace="$NAMESPACE" -o=json | jq '.status' || echo "{}")
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
kubectl logs "jobs/$deployer_name" --namespace="$NAMESPACE" || echo "ERROR Failed to get logs for deployer $deployer_name"
deployer_name=""

echo "INFO Stop the application"
$marketplace_tools/scripts/stop.sh \
  --name="$NAME" \
  --namespace="$NAMESPACE" \
  || clean_and_exit "ERROR Failed to stop application"

deletion_timeout=180
echo "INFO Wait for the applications to be deleted"
timeout --foreground $deletion_timeout "$DIR/wait_for_deletion.sh" "$NAMESPACE" applications \
  || clean_and_exit "ERROR Some applications where not deleted"

echo "INFO Wait for standard resources were deleted."
timeout --foreground $deletion_timeout "$DIR/wait_for_deletion.sh" "$NAMESPACE" all \
  || clean_and_exit "ERROR Some resources where not deleted"

echo "INFO Wait for service accounts to be deleted."
timeout --foreground $deletion_timeout "$DIR/wait_for_deletion.sh" "$NAMESPACE" serviceaccounts,roles,rolebindings \
  || clean_and_exit "ERROR Some service accounts or roles where not deleted"

delete_namespace
