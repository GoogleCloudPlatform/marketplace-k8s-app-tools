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

for i in "$@"
do
case $i in
  --application_uid=*)
    application_uid="${i#*=}"
    shift
    ;;
  --mode=*)
    mode="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "application_uid" ]] && echo "application_uid required" && exit 1

# Assert existence of required environment variables.
[[ -z "APP_INSTANCE_NAME" ]] && echo "APP_INSTANCE_NAME not defined" && exit 1
[[ -z "NAMESPACE" ]] && echo "NAMESPACE not defined" && exit 1

echo "Creating the manifests for the kubernetes resources that build the application \"$APP_INSTANCE_NAME\""

# Perform environment variable expansions.
# Note: We list out all environment variables and explicitly pass them to
# envsubst to avoid expanding templated variables that were not defined
# in this container.
environment_variables="$(printenv \
  | sed 's/=.*$//' \
  | sed 's/^/$/' \
  | paste -d' ' -s)"

data_dir="/data"
manifest_dir="$data_dir/manifest-expanded"
mkdir "$manifest_dir"

# Overwrite the templates using the test templates
if [[ "$mode" = "test" ]]; then
  cp -RT "/data-test" "/data"
fi

# Replace the environment variables placeholders from the manifest templates
for manifest_template_file in "$data_dir"/manifest/*; do
  manifest_file=$(basename "$manifest_template_file" | sed 's/.template$//')
  
  cat "$manifest_template_file" \
    | envsubst "$environment_variables" \
    > "$manifest_dir/$manifest_file" 
done

/bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$application_uid" \
  --manifests "$manifest_dir" \
  --dest "$data_dir/resources.yaml"
