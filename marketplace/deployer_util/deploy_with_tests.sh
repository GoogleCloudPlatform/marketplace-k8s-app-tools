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

# This is the entry point for the test deployment

overlay_test_schema.py \
  --orig "/data-test/schema.yaml" \
  --dest "/data/schema.yaml"
rm /data-test/schema.yaml

/bin/expand_config.py
APP_INSTANCE_NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"

echo "Deploying application \"$APP_INSTANCE_NAME\" in test mode"

application_uid=$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')

create_manifests.sh --application_uid="$application_uid" --mode="test"

separate_tester_jobs.py \
  --manifest "/data/resources.yaml" \
  --test_config "/data-test/config.yaml" \
  --tester_manifest "/data/tester.yaml"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="/data/resources.yaml"

post_success_status.sh

function print_and_fail() {
  message=$1
  echo message
  exit 1
}

wait_timeout=300

# TODO(#53) Consider moving to a separate job
echo "INFO Wait $wait_timeout seconds for the application to get into ready state"
timeout --foreground $wait_timeout wait_for_ready.sh $APP_INSTANCE_NAME $NAMESPACE \
  || print_and_fail "ERROR Application did not get ready before timeout"

tester_manifest="/data/tester.yaml"

# Run test job.
kubectl apply --namespace="$NAMESPACE" --filename="$tester_manifest"

tester_name=$(cat "$tester_manifest" | yj tojson | jq -r '.metadata.name')

start_time=$(date +%s)
poll_interval=4
tester_timeout=30
while true; do
  success=$(kubectl get "jobs/$tester_name" --namespace="$NAMESPACE" -o=json | jq '.status.succeeded' || echo "0")
  if [[ "$success" = "1" ]]; then
    echo "INFO Tester job succeeded"
    break
  fi

  elapsed_time=$(( $(date +%s) - $start_time ))
  if [[ "$elapsed_time" -gt "$tester_timeout" ]]; then
    echo "ERROR Tester job timeout"
    exit 1
  fi

  sleep "$poll_interval"
done

clean_iam_resources.sh
