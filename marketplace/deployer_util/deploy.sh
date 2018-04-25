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

# This is the entry point for the production deployment

/bin/expand_config.py
APP_INSTANCE_NAME="$(/bin/print_config.py --param APP_INSTANCE_NAME)"
NAMESPACE="$(/bin/print_config.py --param NAMESPACE)"

echo "Deploying application \"$APP_INSTANCE_NAME\""

application_uid=$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')

create_manifests.sh --application_uid="$application_uid"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="/data/resources.yaml"

post_success_status.sh

clean_iam_resources.sh
