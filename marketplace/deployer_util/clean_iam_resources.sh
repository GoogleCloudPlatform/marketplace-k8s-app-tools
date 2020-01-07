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

[[ -z "$NAME" ]] && echo "NAME must be set" && exit 1
[[ -z "$NAMESPACE" ]] && echo "NAMESPACE must be set" && exit 1

# Delete the service account (which owns its RBAC objects) by label.
# Update _DEPLOYER_OWNED_KINDS in set_ownership.py to delete additional
# resource types besides Role and RoleBinding.
# Note that only resources of a one-shot deployer have this label.
# Resources of a KALM-managed deployer have
# app.kubernetes.io/component=kalm.marketplace.cloud.google.com label.
kubectl delete --namespace="$NAMESPACE" \
  ServiceAccount \
  -l 'app.kubernetes.io/component'='deployer.marketplace.cloud.google.com','app.kubernetes.io/name'="$NAME" \
  --ignore-not-found
