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

app_uid=$(kubectl get "applications.app.k8s.io/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')
app_api_version=$(kubectl get "applications.app.k8s.io/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.apiVersion}')

# Log information and, at the same time, catch errors early and separately.
# This is a work around for the fact that process and command substitutions
# do not propagate errors.
/bin/expand_config.py --values_mode=raw --app_uid="$app_uid"
echo -n "Application UID: " && print_config.py --xtype APPLICATION_UID --key true && echo ""
echo "=== values.yaml ==="
print_config.py --output=yaml
echo "==================="

for chart in /data/chart/*; do
  # Expand and apply the template for the Application resource.
  # Note: This must be done out-of-band because the Application resource
  # is created before the deployer is invoked, but helm does not handle
  # pre-existing resources.
  /bin/expand_config.py --values_mode=raw --app_uid=""
  helm template \
      --name="$NAME" \
      --namespace="$NAMESPACE" \
      --values=<(print_config.py --output=yaml) \
      --set global.application.spec.addOwnerRef=true
      "$chart" \
    | yaml2json \
    | jq 'select( .kind == "Application" )' \
    | kubectl apply -f -

  # Install the chart.
  # Note: This does not assume that tiller is installed in the cluster;
  # it runs a local tiller process to perform template expansion and
  # hook processing.
  # Note: The local tiller process is configured with --storage=secret,
  # which is recommended but not default behavior.
  /bin/expand_config.py --values_mode=raw --app_uid="$app_uid"
  helm tiller run "$NAMESPACE" -- \
    helm install \
        --name="$NAME" \
        --namespace="$NAMESPACE" \
        --values=<(print_config.py --output=yaml) \
        "$chart"
done
