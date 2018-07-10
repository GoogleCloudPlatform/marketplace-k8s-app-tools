#!/bin/bash

set -xeo pipefail

DIR="$(dirname $0)"

deployer="$(cat "$1" | jq -r .deployer)"
metadata="$(cat "$1" | jq -r .metadata)"

filename=$(basename -- "$1")
filename="${filename%.*}"

mkdir -p data

values="$(realpath data)"/${filename}.yaml

cat $1 | jq -r '.parameters | to_entries[] | "\(.key): \(.value)"' > "$values"

cat "$values"

[[ -z "$metadata" ]] || [[ "$metadata" == "null" ]] || metadata_path="/metadata"

docker run -i --rm \
  --entrypoint=/bin/validate.py \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$values":/data/values.yaml \
  -v "$metadata":/metadata \
  "$deployer" \
  --metadata="$metadata_path"

testParameters=$(echo "$(cat $1 | jq -r '.parameters')" "$(cat $1 | jq -r '.testParameters')" \
    | jq -s '.[0] * .[1]')

echo "$testParameters"

"$DIR/driver.sh" \
 --deployer="$deployer" \
 --parameters="$testParameters"
