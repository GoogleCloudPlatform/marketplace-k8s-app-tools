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

env_vars="$(/bin/print_config.py -o shell_vars)"
APP_INSTANCE_NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"

echo "Creating the manifests for the kubernetes resources that build the application \"$APP_INSTANCE_NAME\""

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
    | /bin/config_env.py envsubst "${env_vars}" \
    > "$manifest_dir/$manifest_file"
done

/bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$application_uid" \
  --manifests "$manifest_dir" \
  --dest "$data_dir/resources.yaml"
