#!/bin/bash

set -eo pipefail

for i in "$@"
do
case $i in
  -h=*)
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
Run the verification on app deployer. The only parameter is a config file in json format, example:

{
  "deployer": <link to the deployer image gcr>, // Required
  "metadata": <path to the metadata file>, // Optional. When not specified, the validation the metadata will be skipped
  "parameters": { // Optional. The parameters to be passed to the deployer. They are app specific
    <key>: <value>,
    ...
  },
  "testParameters": { // Optional. The parameters to be passed to the deployer in test mode. They are app specific.
    <key>: <value>,
    ...
  }
}
EOF
fi

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
