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

# If host kubernetes configuration is mounted, copy it to the container's
# default $KUBECONFIG location after adjusting system-specific fields.
if [[ -e "/mount/config/.kube/config" ]]; then
  mkdir -p "$HOME/.kube"

  # Adjusting cmd-path for gcp auth-providers to this container's gcloud
  # installation location.
  cat /mount/config/.kube/config \
    | yaml2json \
    | jq \
          --arg gcloud "$(readlink -f "$(which gcloud)")" \
          '.users = [ .users[] |
                      if .user["auth-provider"]["name"] == "gcp" and .user["auth-provider"]["config"]["cmd-path"]
                        then .user["auth-provider"]["config"]["cmd-path"] = $gcloud
                        else .
                      end
                    ]' \
  > "$HOME/.kube/config"
fi

# If host gcloud configuration is mounted, replace container gcloud
# configuration with it.
# Note: We do this to ensure the directory is writable without providing
# write access to host gcloud configuration directory.
if [[ -e "/mount/config/.config/gcloud" ]]; then
  rm -rf "$HOME/.config/gcloud"
  cp -r "/mount/config/.config/gcloud" "$HOME/.config"
fi

if [[ "${GCLOUD_ORIGINAL_PATH}" != "" ]]; then
  # Replace gcloud path prefixes with the one mounted in this container.
  # .boto files are the configuration files for gsutil.
  find "$HOME/.config" -name ".boto" \
    | xargs -r -n 1 sed -i "s|^gs_service_key_file = ${GCLOUD_ORIGINAL_PATH}/|gs_service_key_file = $HOME/.config/gcloud/|"
fi

