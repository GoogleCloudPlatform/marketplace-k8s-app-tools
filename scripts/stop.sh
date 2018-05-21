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

for i in "$@"
do
case $i in
  --marketplace_tools=*)
    marketplace_tools="${i#*=}"
    shift
    ;;
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  --parameters=*)
    parameters="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$marketplace_tools" ]] && >&2 echo "--marketplace_tools required" && exit 1
[[ -z "$deployer" ]] && >&2 echo "--deployer required" && exit 1
[[ -z "$parameters" ]] && >&2 echo "--parameters required" && exit 1

# Unpack the deployer schema.
schema="$("$marketplace_tools/scripts/extract_deployer_config_schema.sh" \
	--deployer="$deployer")"

# Parse the config schema for the keys associated with name and namespace.
name_key=$("$marketplace_tools/marketplace/deployer_util/extract_schema_key.py" \
		--schema_file=<(echo "$schema") \
    --type=NAME)
namespace_key=$("$marketplace_tools/marketplace/deployer_util/extract_schema_key.py" \
		--schema_file=<(echo "$schema") \
    --type=NAMESPACE)

# Extract name and namespace from parameters.
name=$(echo "$parameters" \
	| jq --raw-output --arg key "$name_key" '.[$key]')
namespace=$(echo "$parameters" \
	| jq --raw-output --arg key "$namespace_key" '.[$key]')

kubectl delete "application/$name" --namespace="$namespace" --ignore-not-found
