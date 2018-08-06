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
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  --kind=*)
    kind="${i#*=}"
    shift
    ;;
  --timeout=*)
    timeout="${i#*=}"
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

start_time=$(date +%s)
poll_interval=4

while true; do
  # Everything under the namespace needs to be removed after app/uninstall
  echo "INFO Checking if $kind were deleted"
  resources=$(kubectl get $kind \
    --namespace="$namespace" \
    -o=json \
    | jq -r '.items[] | "\(.kind)/\(.metadata.name)"')

  res_count=$(echo $resources | wc -w)

  if [[ "$res_count" -eq 0 ]]; then
    break
  else
    # Ignore service account default
    if [[ "$resources" = "ServiceAccount/default" ]]; then
      break
    else
      echo "INFO Remaining: $res_count"
      echo "INFO $resources"

      elapsed_time=$(( $(date +%s) - $start_time ))
      if [[ "$elapsed_time" -gt "$timeout" ]]; then
        exit 1
      fi

      sleep "$poll_interval"
    fi
  fi
done
