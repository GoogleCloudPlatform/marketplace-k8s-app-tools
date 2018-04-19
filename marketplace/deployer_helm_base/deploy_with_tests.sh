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

# Assert existence of required environment variables.
[[ -v "APP_INSTANCE_NAME" ]] || exit 1
[[ -v "NAMESPACE" ]] || exit 1

# Assign owner references to the existing kubernates resources tagged with the application name
application_uid=$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')

./set_owner_reference_in_cluster.sh --application_uid="$application_uid"

resources_yaml=$(./create_manifests.sh --application_uid="$application_uid" --mode=test)

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="$resources_yaml"
