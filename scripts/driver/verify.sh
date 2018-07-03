#!/bin/bash

set -xeo pipefail

deployer="$(cat "$1" | jq -r .deployer)"
parameters="$(cat "$1" | jq -r .parameters)"
metadata="$(cat "$1" | jq -r .metadata)"

mkdir -p data/values

printf myapp > data/values/name
printf mynamespace > data/values/namespace
printf reportingSecret > data/values/reportingSecret

docker run -i --entrypoint=/bin/validate.py \
-v /var/run/docker.sock:/var/run/docker.sock \
-v $(realpath "../../marketplace/deployer_util/validate.py"):/bin/validate.py \
-v $(realpath "../../marketplace/deployer_util/bash_util.py"):/bin/bash_util.py \
-v $(realpath data/values/name):/data/values/name \
-v $(realpath data/values/namespace):/data/values/namespace \
-v $(realpath data/values/reportingSecret):/data/values/reportingSecret \
-v "$metadata":/metadata \
--rm "$deployer" \
--metadata=/metadata

# ./driver.sh \
#  --deployer="$deployer" \
#  --parameters="$parameters"
