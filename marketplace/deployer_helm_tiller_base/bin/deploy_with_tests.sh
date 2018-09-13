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

/bin/expand_config.py
export NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
export NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"

echo "Deploying application \"$NAME\" in test mode"

app_uid=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')
app_api_version=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.apiVersion}')

patch_assembly_phase.sh --status="Pending"

for chart in /data/chart/*; do
  helm template \
      --name="$NAME" \
      --namespace="$NAMESPACE" \
      --set "template_mode=true" \
      --values=<(print_config.py --output=yaml) \
      "$chart" \
    | yaml2json \
    | jq 'select( .kind == "Application" )' \
    | kubectl apply -f -

  helm tiller run "$NAMESPACE" -- \
    helm install \
        --name="$NAME" \
        --namespace="$NAMESPACE" \
        --values=<(print_config.py --output=yaml) \
        "$chart"
done

patch_assembly_phase.sh --status="Success"

wait_for_ready.py \
  --name $NAME \
  --namespace $NAMESPACE \
  --timeout 300

clean_iam_resources.sh
