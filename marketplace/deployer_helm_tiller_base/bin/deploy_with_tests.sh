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

set -eox pipefail

# This is the entry point for the test deployment

NAME="$(/bin/print_config.py \
  --xtype NAME \
  --values_mode raw)"
NAMESPACE="$(/bin/print_config.py \
  --xtype NAMESPACE \
  --values_mode raw)"
export NAME
export NAMESPACE

/bin/deploy_internal.sh

patch_assembly_phase.sh --status="Success"

wait_for_ready.py \
  --name $NAME \
  --namespace $NAMESPACE \
  --timeout 300

helm tiller run "$NAMESPACE" -- helm test "$NAME"

clean_iam_resources.sh
