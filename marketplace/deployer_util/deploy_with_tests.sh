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
rm -f /data-test/schema.yaml

/bin/expand_config.py
export NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
export NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"

echo "Deploying application \"$NAME\" in test mode"

application_uid=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')

create_manifests.sh --application_uid="$application_uid" --mode="test"

separate_tester_resources.py \
  --appuid "$application_uid" \
  --appname "$NAME" \
  --manifest "/data/resources.yaml" \
  --tester_manifest "/data/tester.yaml"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="/data/resources.yaml"

patch_assembly_phase.sh --status="Success"

wait_for_ready.py \
  --name $NAME \
  --namespace $NAMESPACE \
  --timeout 300

tester_manifest="/data/tester.yaml"
if [[ -e "$tester_manifest" ]]; then
  cat $tester_manifest

  run_tester.py \
    --namespace $NAMESPACE \
    --manifest $tester_manifest
fi

clean_iam_resources.sh
