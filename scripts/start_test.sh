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
  --test_parameters=*)
    test_parameters="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

parameters=$(echo "$parameters" "$test_parameters" | jq -s '.[0] * .[1]')
entrypoint="/bin/deploy_with_tests.sh"

"$marketplace_tools"/scripts/start.sh \
  --marketplace_tools="$marketplace_tools" \
  --deployer="$deployer" \
  --parameters="$parameters" \
  --entrypoint="$entrypoint"
