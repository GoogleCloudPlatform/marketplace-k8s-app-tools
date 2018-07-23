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
  --tag=*)
    tag="${i#*=}"
    shift
    ;;
  --latest)
    latest=1
    shift
    ;;
  -h)
    h=1
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

if [[ "$h" ]]; then
  cat <<EOF
Builds the base deployer images and push them to gcr.io. 

Usage:
publish_deployers.sh --tag=v0.5 --latest

Arguments:
  --tag    The git tag to be published. Make sure that the tag is already created.
  --latest If present, the images will be pushed to the latest tag as well.
EOF
exit 0
fi

git fetch --tags

if [[ -z "$tag" ]]; then 
  echo "Specify --tag"
  git tag | grep -E '^v[0-9]+(\.[0-9]+)*$'
  exit 1
else
  # Makes sure that the select tag exists
  git tag | grep -w "$tag"
fi

git checkout "$tag"

changes="$(git status --porcelain)"
if [[ ! -z "$changes" ]]; then
  echo "Make sure there are no pending changes"
  exit 1
fi

make -B .build/marketplace/deployer/envsubst
make -B .build/marketplace/deployer/helm

commit="$(git rev-parse HEAD | fold -w 12 | head -n 1)"
image_tag="$tag-$commit"

for name in deployer_envsubst deployer_helm; do \
  docker tag \
      "gcr.io/cloud-marketplace-tools/k8s/$name:latest" \
      "gcr.io/cloud-marketplace-tools/k8s/$name:$image_tag"
  docker push "gcr.io/cloud-marketplace-tools/k8s/$name:$image_tag"; \

  [[ "$latest" ]] && push "gcr.io/cloud-marketplace-tools/k8s/$name:latest"
done
