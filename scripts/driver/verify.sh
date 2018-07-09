#!/bin/bash

set -xeo pipefail

deployer="$(cat "$1" | jq -r .deployer)"
parameters="$(cat "$1" | jq -r .parameters)"
metadata="$(cat "$1" | jq -r .metadata)"

rm -rf data
mkdir -p data/values

printf "name: myapp\n" >> data/values.yaml
printf "namespace: mynamespace\n" >> data/values.yaml
printf "reportingSecret: reportingSecret\n" >> data/values.yaml
printf "serviceAccount.name: kasten-sa\n" >> data/values.yaml

cat data/values.yaml

# docker run -i --rm --entrypoint=/bin/validate.py \
#   -v /var/run/docker.sock:/var/run/docker.sock \
#   -v "$(realpath "../../marketplace/deployer_util/validate.py")":/bin/validate.py \
#   -v "$(realpath "../../marketplace/deployer_util/bash_util.py")":/bin/bash_util.py \
#   -v "$(realpath data/values.yaml)":/data/values.yaml \
#   -v "$metadata":/metadata \
#   "$deployer" \
#   --metadata=/metadata

./driver.sh \
 --deployer="$deployer" \
 --parameters="$parameters"
