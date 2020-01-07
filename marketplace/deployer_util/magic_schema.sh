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

set -eo pipefail

for i in "$@"
do
case $i in
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$deployer" ]] && >&2 echo "--deployer required" && exit 1

name_key="$(/bin/extract_schema_key.py --type NAME)"
namespace_key="$(/bin/extract_schema_key.py --type NAMESPACE)"

# Provision resources with magic name and namespaces.
# Provisioned manifests are inserted into the original schema
# under top-level __manifests__ field.
printf '{%s: "m4g1cn8m3", %s: "m4g1cn8m32p4c3"}' "${name_key}" "${namespace_key}" \
  | /bin/provision.py --values_mode=stdin --deployer_image="${deployer}" --deployer_service_account_name='m4g1cn8m3-deployer-sa' \
  | /bin/set_app_labels.py --manifests=- --dest=- --name="m4g1cn8m3" --namespace="m4g1cn8m32p4c3" \
  | /bin/yaml2json \
  | jq -s . \
  | jq '{"__manifests__": .}' \
  | jq -s '.[0] * .[1]' <(cat /data/schema.yaml | /bin/yaml2json) - \
  | /bin/json2yaml
