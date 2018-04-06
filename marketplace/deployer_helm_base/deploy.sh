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

# Assert existence of required environment variables.
[[ -v "APP_INSTANCE_NAME" ]] || exit 1
[[ -v "NAMESPACE" ]] || exit 1

# Expand the chart template.
mkdir "/manifest-expanded"
for chart in /data/chart/*; do
  chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//').yaml
  helm template "$chart" \
        --name="$APP_INSTANCE_NAME" \
        --namespace="$NAMESPACE" \
        --set="APP_INSTANCE_NAME=$APP_INSTANCE_NAME,NAMESPACE=$NAMESPACE" \
    > "/manifest-expanded/$chart_manifest_file"
done

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="/manifest-expanded"
