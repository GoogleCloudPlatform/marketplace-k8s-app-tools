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
  --status=*)
    status="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$status" ]] && >&2 echo "--status required" && exit 1

if ! [[ "$status" =~ ^(Pending|Success|Failed)$ ]]; then
  echo "Expected --status to be Pending, Success, or Failed. Got: $status"
  exit 1
fi

APP_INSTANCE_NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"


echo "Marking deployment of application \"$APP_INSTANCE_NAME\" as \"$status\"."

kubectl patch "applications/$APP_INSTANCE_NAME" \
  --namespace="$NAMESPACE" \
  --type=merge \
  --patch "{\"spec\": {\"assemblyPhase\": \"$status\"}}"
