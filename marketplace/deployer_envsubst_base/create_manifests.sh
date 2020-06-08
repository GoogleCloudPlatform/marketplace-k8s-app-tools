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

[[ -z "$NAME" ]] && echo "NAME must be set" && exit 1
[[ -z "$NAMESPACE" ]] && echo "NAMESPACE must be set" && exit 1

env_vars="$(/bin/print_config.py -o shell_vars)"

echo "Creating the manifests for the kubernetes resources that build the application \"$NAME\""

data_dir="/data"
manifest_dir="$data_dir/manifest-expanded"
mkdir "$manifest_dir"

# Overwrite the templates using the test templates
if [[ "$mode" = "test" ]]; then
  if [[ -e "/data-test/manifest" ]]; then
    cp -RT "/data-test/manifest" "/data/manifest"
  else
    echo "$LOG_SMOKE_TEST INFO No overriding manifests found at /data-test/manifest."
  fi
fi

# Replace the environment variables placeholders from the manifest templates
for manifest_template_file in "$data_dir"/manifest/*; do
  manifest_file=$(basename "$manifest_template_file" | sed 's/.template$//')
  cat "$manifest_template_file" \
    | /bin/config_env.py envsubst "${env_vars}" \
    > "$manifest_dir/$manifest_file"

  ensure_k8s_apps_labels.py \
  --manifest "$manifest_dir/$manifest_file" \
  --appname "$NAME"
done
