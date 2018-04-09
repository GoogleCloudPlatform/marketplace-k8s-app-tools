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

set -e
set -o pipefail
set -x

# Assert existence of required environment variables.
[[ -v "APP_INSTANCE_NAME" ]] || exit 1
[[ -v "NAMESPACE" ]] || exit 1

# Perform environment variable expansions.
# Note: We list out all environment variables and explicitly pass them to
# envsubst to avoid expanding templated variables that were not defined
# in this container. In this manner, other containers can use a envsubst
# for variable expansion, provided the variable names do not conflict.
environment_variables="$(printenv \
  | sed 's/=.*$//' \
  | sed 's/^/$/' \
  | paste -d' ' -s)"

datadir="/data"
manifestdir="$datadir/manifest-expanded"
mkdir $manifestdir

# Replace the environment variables placeholders from the manifest templates
for manifest_template_file in $datadir/manifest/*; do
  manifest_file=$(basename "$manifest_template_file" | sed 's/.template$//')
  
  cat "$manifest_template_file" \
    | envsubst "$environment_variables" \
    > "$manifestdir/$manifest_file" 
done

# Apply owner references
APPLICATION_UID="$(kubectl get "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')"

resourcesyaml="$datadir/resources.yaml"
python /bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$APPLICATION_UID" \
  --manifests "$manifestdir" \
  --dest "$resourcesyaml"

# Apply the manifest.
kubectl apply --namespace="$NAMESPACE" --filename=$resourcesyaml
