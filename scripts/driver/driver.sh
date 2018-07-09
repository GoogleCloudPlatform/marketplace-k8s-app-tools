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
[[ -z "$wait_timeout" ]] && wait_timeout=600

# Getting the directory of the running script
DIR="$(dirname $0)"
echo $DIR

namespace_key="$(docker run --entrypoint=/bin/extract_schema_key.py --rm "$deployer" --type NAMESPACE)"
NAME="$(echo "$parameters" \
    | docker run -i --entrypoint=/bin/print_config.py --rm "$deployer" \
    --values_file=- --param '{"x-google-marketplace": {"type": "NAME"}}')"

# use base64 for BSD systems where tr won't handle illegal characters
export NAMESPACE="apptest-$(cat /dev/urandom \
    | base64 \
    | tr -dc 'a-z0-9' \
    | fold -w 8 \
    | head -n 1)"
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

parameters=$(echo "$parameters" \
  | jq \
    --arg namespace_key "$namespace_key" \
    --arg namespace "$NAMESPACE" \
    '.[$namespace_key] = $namespace')

echo "INFO Parameters: $parameters"

echo "INFO Initializes the deployer container which will deploy all the application components"
$DIR/../start.sh \
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
  printf "Elapsed ${elapsed_time}s\r"
  if [[ "$elapsed_time" -gt "$wait_timeout" ]]; then
    clean_and_exit "ERROR Deployer job timeout"
  fi

  sleep "$poll_interval"
done

# Get the logs from the deployer before deleting the application. Set deployer name to empty so clean up doesn't try to get its logs again.
kubectl logs "jobs/$deployer_name" --namespace="$NAMESPACE" || echo "ERROR Failed to get logs for deployer $deployer_name"
deployer_name=""

echo "INFO Stop the application"
$DIR/../stop.sh \
  --name="$NAME" \
  --namespace="$NAMESPACE" \
  || clean_and_exit "ERROR Failed to stop application"

deletion_timeout=180
echo "INFO Wait for the applications to be deleted"
"$DIR/wait_for_deletion.sh" \
  --namespace="$NAMESPACE" \
  --kind=applications \
  --timeout="$deletion_timeout" \
  || clean_and_exit "ERROR Some applications where not deleted"

echo "INFO Wait for standard resources were deleted."
"$DIR/wait_for_deletion.sh" \
  --namespace="$NAMESPACE" \
  --kind=all \
  --timeout="$deletion_timeout" \
  || clean_and_exit "ERROR Some resources where not deleted"

echo "INFO Wait for service accounts to be deleted."
"$DIR/wait_for_deletion.sh" \
  --namespace="$NAMESPACE" \
  --kind=serviceaccounts,roles,rolebindings \
  --timeout="$deletion_timeout" \
  || clean_and_exit "ERROR Some service accounts or roles where not deleted"

delete_namespace
