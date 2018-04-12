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

# Perform environment variable expansions.
# Note: We list out all environment variables and explicitly pass them to
# envsubst to avoid expanding templated variables that were not defined
# in this container.
environment_variables="$(printenv \
  | sed 's/=.*$//' \
  | sed 's/^/$/' \
  | paste -d' ' -s)"

# Expand the chart template.
mkdir "/manifest-expanded"
for chart in /data/chart/*; do
  # TODO(trironkk): Construct values.yaml directly from ConfigMap, rather than
  # stitching into values.yaml.template first.
  tar -xf "$chart" "chart/values.yaml.template"
  cat "chart/values.yaml.template" \
    | envsubst "$environment_variables" \
    > "values.yaml"

  chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//').yaml
  helm template "$chart" \
        --name="$APP_INSTANCE_NAME" \
        --namespace="$NAMESPACE" \
        --values="values.yaml" \
    > "/manifest-expanded/$chart_manifest_file"

  rm "chart/values.yaml.template" "values.yaml"
done

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename="/manifest-expanded"
