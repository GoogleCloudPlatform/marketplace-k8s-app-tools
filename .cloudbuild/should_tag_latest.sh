#!/bin/bash

# Determines if the "latest" tag should be on the local tag.
# Outputs "true or false".
#
# It pulls down the tags that are currently available remotely.
# Among those and the new local tag, the highest version is picked
# to be tagged as "latest".
# We're only considering SemVer major.minor.patch tags.
# Usage:
#   tag_latest.sh <repo name> <local tag>
# For example:
#   tag_latest.sh gcr.io/$PROJECT_ID/testrunner "0.1.3"
#   tag_latest.sh gcr.io/$PROJECT_ID/testrunner $TAG_NAME

set -eu

readonly repo="$1"
readonly local_tag="$2"

# Verify that the local tag is a non-prerelease SemVer.
# Note that we should never tag a prerelease version as latest.
# A prerelease version looks like 1.3.5-beta.
if [[ -z "$(echo "$local_tag" | egrep '^[0-9]+\.[0-9]+\.[0-9]+$')" ]]; then
  echo "Local tag $local_tag is not a valid non-prerelease SemVer" >&2
  echo "false"
  exit
fi

latest_remote_version=$( \
  gcloud container images list-tags "$repo" \
    --format "value(tags)" --filter 'tags~\d+\.\d+\.\d+'\
    | tr ',' '\n' \
    | egrep '^[0-9]+\.[0-9]+\.[0-9]+$' \
    | sort -t '.' -k 1,1 -k 2,2 -k 3,3 -g \
    | tail -n 1)
echo "Latest remote version: $latest_remote_version" >&2
latest_version=$( \
  printf '%s\n%s' "$latest_remote_version" "$local_tag" \
    | sort -t '.' -k 1,1 -k 2,2 -k 3,3 -g \
    | tail -n 1)
echo "Latest version should be: $latest_version" >&2

# If the tag is not the local tag, we need to pull it down
# before tagging "latest" locally.
if [[ "$local_tag" != "$latest_version" ]]; then
  echo "false"
else
  echo "true"
fi
