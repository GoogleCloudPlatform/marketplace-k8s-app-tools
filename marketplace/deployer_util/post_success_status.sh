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

APP_INSTANCE_NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"

echo "Marking deployment of application \"$APP_INSTANCE_NAME\" as succeeded."

# --output=json is used to force kubectl to succeed even if the patch command
# makes not change to the resource. Otherwise, this command exits 1.
kubectl patch "applications/$APP_INSTANCE_NAME" \
  --output=json \
  --namespace="$NAMESPACE" \
  --type=merge \
  --patch "metadata:
             annotations:
               kubernetes-engine.cloud.google.com/application-deploy-status: Succeeded"
