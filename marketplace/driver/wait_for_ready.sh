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

ready="false"

app=$1
namespace=$2

# echo "INFO Wait for $app to get ready"
# while [[ "$ready" != "true" ]]; do

#   echo "INFO kubectl get Application/$app --namespace=\"$namespace\" -o=jsonpath='{.metadata.ApplicationStatus.ready}'"

#   ready=$(kubectl get "Application/$app" --namespace="$namespace" -o=jsonpath='{.metadata.ApplicationStatus.ready}')
  
#   if [[ "$ready" = "true" ]]; then
#     echo "INFO Application/$app is ready"
#   else 
#   	sleep 4
#   fi
# done

echo "INFO Look for tester job"
while [[ "$ready" != "true" ]]; do

  echo "INFO kubectl get Application/$app --namespace=\"$namespace\" -o=jsonpath='{.metadata.ApplicationStatus.ready}'"

  ready=$(kubectl get "Application/$app" --namespace="$namespace" -o=jsonpath='{.metadata.ApplicationStatus.ready}')
  
  if [[ "$ready" = "true" ]]; then
    echo "INFO Application/$app is ready"
  else 
    sleep 4
  fi
done