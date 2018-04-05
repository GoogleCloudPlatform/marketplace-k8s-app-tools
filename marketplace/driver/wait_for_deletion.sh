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

namespace=$1
kind=$2
deleted=false

while [[ "$deleted" = "false" ]]; do
  # Everything under the namespace needs to be removed after app/uninstall
  echo "INFO Checking if $kind were deleted"
  resources=$(kubectl get $kind \
    --namespace="$namespace" \
    -o=json \
    | jq -r '.items[] | "\(.kind)/\(.metadata.name)"')

  rescount=$(echo $resources | wc -w)

  if [[ "$rescount" = "0" ]]; then
    deleted=true
  else
    # Ignore service account default
    if [[ "$resources" = "ServiceAccount/default" ]]; then
      deleted=true
    else
      echo "INFO Remaining: $rescount"
      echo "INFO $resources"
      sleep 4
    fi
  fi
done