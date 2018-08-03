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


function get_image_tag() {
  # Go to marketplace-tools repository
  cd $(readlink -f "$(dirname "${BASH_SOURCE[0]}")")
  # Set the image tag as the git tag
  image_tag="$(git tag --points-at HEAD | grep -E '^v[0-9]+(\.[0-9]+)*$' | head -n 1 || echo "")"

  # If commit is not tagged, set image tag to commit hash
  [[ -z "$image_tag" ]] && image_tag="$(git rev-parse HEAD | fold -w 12 | head -n 1)"
  # Return to previous location
  cd - > /dev/null
  echo $image_tag
}
