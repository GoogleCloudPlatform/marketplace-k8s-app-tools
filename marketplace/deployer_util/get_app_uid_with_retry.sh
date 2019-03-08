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

# If Istio is enabled, it will take a few seconds before we can call the k8s API.
# Instead of checking if Istio is enabled, it is simple to poll for 30s until
# it works or a specified timeout.
# https://github.com/istio/istio/issues/12187.

start_time=$(date +%s)
poll_interval=1
timeout=30

while [[ -z "$app_uid" ]]; do
  app_uid=$(kubectl get "applications/$NAME" \
    --namespace="$NAMESPACE" \
    --output=jsonpath='{.metadata.uid}') || true

  if [[ -z "$app_uid" ]]; then
    elapsed_time=$(( $(date +%s) - $start_time ))
    if [[ "$elapsed_time" -gt "$timeout" ]]; then
      echo "Failed to get app_uid"
      exit 1
    fi

    sleep "$poll_interval"
  fi
done

echo $app_uid
