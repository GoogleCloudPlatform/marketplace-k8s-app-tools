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
      | envsubst "$environment_variables" \
      > "$extracted/$chart_manifest_file/chart/values.yaml"
  done
}

extract_manifest "$data_dir"

# Overwrite the templates using the test templates
if [[ "$mode" = "test" ]]; then
  test_data_dir="/data-test"

  extract_manifest "$test_data_dir"

  cp -RT "$test_data_dir/extracted" "$data_dir/extracted"
fi

for chart in "$data_dir/extracted"/*; do
  chart_manifest_file=$(basename "$chart" | sed 's/.tar.gz$//').yaml

  helm template "$chart/chart" \
    --name="$APP_INSTANCE_NAME" \
    --namespace="$NAMESPACE" \
    > "$manifest_dir/$chart_manifest_file"
done


resources_yaml="$data_dir/resources.yaml"
python /bin/setownership.py \
  --appname "$APP_INSTANCE_NAME" \
  --appuid "$application_uid" \
  --manifests "$manifest_dir" \
  --dest "$resources_yaml"

echo "$resources_yaml"
