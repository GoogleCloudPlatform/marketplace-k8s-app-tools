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

set -x

for i in "$@"
do
case $i in
  --app_name=*)
    app_name="${i#*=}"
    shift
    ;;
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  --marketplace_tools=*)
    marketplace_tools="${i#*=}"
    shift
    ;;
  --tester_timeout=*)
    tester_timeout="${i#*=}"
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$app_name" ]] && echo "--app-name required" && exit 1
[[ -z "$deployer" ]] && echo "--deployer required" && exit 1
[[ -z "$marketplace_tools" ]] && echo "--marketplace_tools required" && exit 1
[[ -z "$tester_timeout" ]] && tester_timeout=300

# Getting the directory of the running script
DIR=$(dirname $0)
echo $DIR

NAMESPACE="apptest-$(uuidgen)"
APP_INSTANCE_NAME="${app_name}-1"

echo "INFO Creates namespace \"$NAMESPACE\""
kubectl create namespace "$NAMESPACE"

[[ $? -ne 0 ]] && exit 1

function delete_namespace() {
  echo "INFO Collecting events for namespace \"$NAMESPACE\""
  kubectl get events --namespace=$NAMESPACE
  echo "INFO Deleting namespace \"$NAMESPACE\""
  kubectl delete namespace $NAMESPACE
}

function clean_and_exit() {
  delete_namespace
  exit 1
}

echo "INFO Creates the Application CRD in the namespace"
kubectl apply -f "$marketplace_tools/crd/application-resource-definition.yaml"

echo "INFO Initializes the deployer container which will deploy all the application components"
$marketplace_tools/scripts/start.sh \
  --name=$APP_INSTANCE_NAME \
  --namespace=$NAMESPACE \
  --deployer=$deployer \
  || clean_and_exit


echo "INFO Wait for tester job to succeed before $tester_timeout seconds"
poll_interval=4
waited=0
while [[ $waited -lt $tester_timeout ]]; do
  succeeded=$(kubectl get jobs --selector=tester=true -o=json --namespace="$NAMESPACE" | jq -r '.items[].status.succeeded')
  
  if [[ "$succeeded" = "1" ]]; then
    echo "INFO Tester job suceeded"
    break
  else 
    sleep $poll_interval
    waited=$((waited+poll_interval))
  fi
done

if [[ "$succeeded" != "1" ]]; then
  echo "ERROR Tester has not run to completition."
  tester_job_name=$(kubectl get jobs --selector=tester=true -o=json --namespace="$NAMESPACE" | jq -r '.items[].metadata.name')
  [[ -z "$tester_job_name" ]] && echo "ERROR tester job not found" && clean_and_exit

  echo  $(kubectl logs jobs/"$tester_job_name" --namespace="$NAMESPACE") \
    || true
  clean_and_exit
fi

# echo "INFO Wait $wait_timeout seconds for the application to get into ready state"
# timeout --foreground $wait_timeout $DIR/./wait_for_ready.sh $APP_INSTANCE_NAME $NAMESPACE \
#   || echo "ERROR Application did not get ready before timeout"
#   && clean_and_exit

# echo "INFO Make sure that the app stays in ready state for $success_timeout seconds"
# poll_interval=4
# waited=0
# while [[ $waited -lt $success_timeout ]]; do

#   echo "INFO kubectl get Application/$APP_INSTANCE_NAME --namespace=\"$NAMESPACE\" -o=jsonpath='{.metadata.ApplicationStatus.ready}'"

#   ready=$(kubectl get "Application/$APP_INSTANCE_NAME" --namespace="$NAMESPACE" -o=jsonpath='{.metadata.ApplicationStatus.ready}')
  
#   if [[ "$ready" = "true" ]]; then
#     sleep $poll_interval
#     waited=$((waited+poll_interval))
#   else 
#     echo "ERROR Application reverted to not ready state"
#     exit 1
#   fi
# done

echo "INFO Stop the application"
$marketplace_tools/scripts/stop.sh \
      --name=$APP_INSTANCE_NAME \
      --namespace=$NAMESPACE

exitcode=0

echo "INFO Wait for the applications to be deleted"
timeout --foreground 20 $DIR/./wait_for_deletion.sh $NAMESPACE applications

if [[ $? -ne 0 ]]; then 
  echo "ERROR Some applications where not deleted"
  exitcode=1
fi

echo "INFO Wait for standard resources were deleted."
timeout --foreground 20 $DIR/./wait_for_deletion.sh $NAMESPACE all

if [[ $? -ne 0 ]]; then 
  echo "ERROR Some resources where not deleted"
  exitcode=1
fi

echo "INFO Wait for service accounts to be deleted."
timeout --foreground 20 $DIR/./wait_for_deletion.sh $NAMESPACE serviceaccounts,roles,rolebindings

if [[ $? -ne 0 ]]; then 
  echo "ERROR Some service accounts or roles where not deleted"
  exitcode=1
fi

if [[ "$exitcode" = "0" ]]; then
  echo "INFO Success"
else
  echo "ERROR Some validation steps have failed"
fi

delete_namespace

exit $exitcode
