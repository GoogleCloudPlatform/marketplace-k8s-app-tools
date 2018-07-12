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

set -xeo pipefail

branch="$1"

[[ -z "$1" ]] && branch="master"

selected_branch="$(git branch | grep "*" | sed s/"* "/""/g)"

[[ "$selected_branch" != "$branch" ]] && echo "Checkout to $branch branch" && exit 1

changes="$(git status --porcelain)"

if [[ ! -z "$changes" ]]; then
  echo "Make sure there are no pending changes"
  exit 1
fi

git pull

diff="$(git diff $branch origin/$branch)"

if [[ ! -z "$diff" ]]; then
  echo "Make sure all changes are pushed to $branch"
  exit 1
fi

rm -f .build/marketplace/deployer/envsubst
rm -f .build/marketplace/deployer/helm

make images/deployer
