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
  --parameters=*)
    parameters="${i#*=}"
    shift
    ;;
  --wait_timeout=*)
    wait_timeout="${i#*=}"
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$deployer" ]] && deployer="$APP_DEPLOYER_IMAGE"
[[ -z "$parameters" ]] && parameters="{}"
[[ -z "$wait_timeout" ]] && wait_timeout=600

docker run \
    --interactive \
    --tty \
    --volume "/var/run/docker.sock:/var/run/docker.sock:ro" \
    --volume "${KUBECONFIG:-$HOME/.kube}:/root/mount/.kube:ro" \
    --volume "$HOME/.config/gcloud:/root/.config/gcloud:ro" \
    --rm \
    "gcr.io/cloud-marketplace-tools/k8s/dev" \
    -- \
    /scripts/driver/driver_internal.sh \
          --deployer="$deployer" \
          --parameters="$parameters" \
          --wait_timeout="$wait_timeout"
