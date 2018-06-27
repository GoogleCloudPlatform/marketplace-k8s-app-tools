#!/bin/bash

set -xeo pipefail

deployer="$(cat "$1" | jq -r .deployer)"
parameters="$(cat "$1" | jq -r .parameters)"

./driver.sh \
  --deployer="$deployer" \
  --parameters="$parameters"
