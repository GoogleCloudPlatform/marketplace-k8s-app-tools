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

# There are the following scenarios:
# - FORCE_MARKETPLACE_TOOLS_TAG, if defined, takes highest precedence.
# - If the tools path is not a git repo, error out.
#   FORCE_MARKETPLACE_TOOLS_TAG must be used in this case.
# - If the git repo is dirty, hash all pending changes and create
#   a tag of "local_MD5_HASH_OF_PENDING_CHANGES"
# - If the git repo is clean, use the commit ID of HEAD.
#   Note that in this case there are 2 scenarios: the commit ID might
#   match something upstream, or it's a local commit. If it's the
#   latter, the docker images are not readily available for pulling.
#   Handling of this case is out of the scope of this script.

# Prints git status.
function status() {
  git status --porcelain -uall 2> /dev/null
}

# Prints current git HEAD commit ID.
function head() {
  git rev-parse HEAD 2> /dev/null
}

# Hash all dirty files.
function hashall() {
  # Include the current checked-out commit in the hash.
  git rev-parse --git-dir HEAD
  while IFS= read -r line; do
    # Remove the status column.
    file=${line:3}
    fullfile="$(git rev-parse --show-toplevel)/$file"
    echo $fullfile
    if [[ -f "$fullfile" ]]; then
      git hash-object $fullfile
    fi
  done < <(status)
}

if [ ! -z "${FORCE_MARKETPLACE_TOOLS_TAG}" ]; then
  >&2 echo "====== NOTICE ======"
  >&2 echo "Using manual override of MARKETPLACE_TOOLS_TAG env var."
  >&2 echo "===================="
  echo -n "${FORCE_MARKETPLACE_TOOLS_TAG}"
  exit 0
fi


if [[ "$(status)" == "" ]] && [[ "$(head)" == "" ]]; then
  # We are not in a git repo.

  >&2 echo "====== ERROR ======"
  >&2 echo "marketplace-k8s-app-tools is not a git repo or submodule."
  >&2 echo "Hope you know what you're doing!"
  >&2 echo "Set the following env var to override:"
  >&2 echo ""
  >&2 echo "export FORCE_MARKETPLACE_TOOLS_TAG=latest"
  >&2 echo ""
  >&2 echo "==================="
  exit 1
fi

if [[ ! -z "$(status)" ]]; then
  # Git is dirty. MD5 the hash of status.
  hash="$(hashall | md5sum | cut -f1 -d' ')"
  echo -n "local_${hash}"
else
  echo -n "sha_$(head)"
fi

