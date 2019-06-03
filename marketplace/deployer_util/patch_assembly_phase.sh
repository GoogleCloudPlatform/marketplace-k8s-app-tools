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

[[ -z "$NAME" ]] && echo "NAME must be set" && exit 1
[[ -z "$NAMESPACE" ]] && echo "NAMESPACE must be set" && exit 1


echo "Marking deployment of application \"$NAME\" as \"$status\"."

if [[ "$status" == "Success" ]]; then
  published_version="$(print_published_version.py --empty_if_not_supported)"
  if ! [[ -z "$published_version" ]]; then
    # Ensure that the application resource has a version
    # matching the declared published version.
    app_version="$(kubectl get "applications.app.k8s.io/$NAME" --output=json \
      | jq -r .spec.descriptor.version)"
    if [[ "$app_version" != "$published_version" ]]; then
      echo "Application's version '$app_version' does not match the declared" \
        "publishedVersion '$published_version' in schema.yaml."
      exit 1
    fi
  fi
fi

# --output=json is used to force kubectl to succeed even if the patch command
# makes not change to the resource. Otherwise, this command exits 1.
kubectl patch "applications.app.k8s.io/$NAME" \
  --output=json \
  --namespace="$NAMESPACE" \
  --type=merge \
  --patch "{\"spec\": {\"assemblyPhase\": \"$status\"}}"
