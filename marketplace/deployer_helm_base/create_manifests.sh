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

# Extract the config values into VAR=VALUE array.
env_vars=($(/bin/print_config.py -o shell))
APP_INSTANCE_NAME="$(/bin/print_config.py --param APP_INSTANCE_NAME)"
NAMESPACE="$(/bin/print_config.py --param NAMESPACE)"

echo "Creating the manifests for the kubernetes resources that build the application \"$APP_INSTANCE_NAME\""

data_dir="/data"
manifest_dir="$data_dir/manifest-expanded"
mkdir -p "$manifest_dir"

function extract_manifest() {
  data=$1
  extracted="$data/extracted"
  mkdir -p "$extracted"

  # Expand the chart template.
  for chart in "$data"/chart/*; do
    # TODO(trironkk): Construct values.yaml directly from ConfigMap, rather than
    # stitching into values.yaml.template first.
    chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//')
    mkdir "$extracted/$chart_manifest_file"
    tar xfC "$chart" "$extracted/$chart_manifest_file"
    cat "$extracted/$chart_manifest_file/chart/values.yaml.template" \
      | eval ${env_vars[@]} envsubst \
      > "$extracted/$chart_manifest_file/chart/values.yaml"
  done
}

extract_manifest "$data_dir"

# Overwrite the templates using the test templates
if [[ "$mode" = "test" ]]; then
  test_data_dir="/data-test"

  extract_manifest "$test_data_dir"

  overlay_test_files.py \
    --manifest "$data_dir/extracted" \
    --test_manifest "$test_data_dir/extracted"
fi

# Run helm expantion on the extracted files
for chart in "$data_dir/extracted"/*; do
  chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//').yaml

  helm template "$chart/chart" \
    --name="$APP_INSTANCE_NAME" \
    --namespace="$NAMESPACE" \
    > "$manifest_dir/$chart_manifest_file"
done

/bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$application_uid" \
  --manifests "$manifest_dir" \
  --dest "$data_dir/resources.yaml"
