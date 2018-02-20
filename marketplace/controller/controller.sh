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

set -e
set -x

[[ -z "$APPLICATION_NAME" ]] && exit 1
[[ -z "$NAMESPACE" ]] && exit 1

report_status() {
  event_name="$APPLICATION_NAME-$(date '+%s%S')"
  event_reason="Cloud Marketplace"
  event_type="$1"
  event_message="$2"
  event_timestamp="$(date '+%Y-%m-%dT%H:%M:%SZ')"

  kubectl apply --namespace="$NAMESPACE" --filename=- <<EOF
apiVersion: v1
firstTimestamp: $event_timestamp
lastTimestamp: $event_timestamp
involvedObject:
  apiVersion: marketplace.cloud.google.com/v1
  kind: Application
  namespace: $NAMESPACE
  name: $APPLICATION_NAME
  uid: $APPLICATION_UID
kind: Event
metadata:
  name: $event_name
  labels:
    app: "$APPLICATION_NAME"
reason: $event_reason
message: $event_message
source:
  component: "$APPLICATION_NAME-operator"
type: Normal
EOF

  kubectl patch "applications/$APPLICATION_NAME" \
    --namespace="$NAMESPACE" \
    --type=merge \
    --patch "metadata:
               annotations:
                 marketplace.cloud.google.com/status:
                   $event_type: $event_message" || true
}

function is_healthy() {
  resource="$1"
  kind=${resource%/*}
  name=${resource#*/}
  case "$kind" in
    Deployment)
      ready_replicas=$(kubectl get "deployments/$name" \
          --namespace="$NAMESPACE" \
          --output=jsonpath='{.status.readyReplicas}')
      total_replicas=$(kubectl get "deployments/$name" \
          --namespace="$NAMESPACE" \
          --output=jsonpath='{.spec.replicas}')
      if [[ "$ready_replicas" == "$total_replicas" ]]; then
        echo "true"; return
      fi
      ;;
    PersistentVolumeClaim)
      phase=$(kubectl get "persistentvolumeclaims/$name" \
          --namespace="$NAMESPACE" \
          --output=jsonpath='{.status.phase}')
      if [[ "$phase" == "Bound" ]]; then
        echo "true"; return
      fi
      ;;
    Service)
      service_type=$(kubectl get "services/$name" \
          --namespace="$NAMESPACE" \
          --output=jsonpath='{.spec.type}')
      if [[ "$service_type" != "LoadBalancer" ]]; then
        echo "true"; return
      fi
      service_ip=$(kubectl get "services/$name" \
          --namespace="$NAMESPACE" \
          --output=jsonpath='{.status.loadBalancer.ingress[].ip}')
      if [[ ! -z "$service_ip" ]]; then
        echo "true"; return
      fi
      ;;
    *)
      # TODO(trironkk): Handle more resource types.
      echo "true"; return
      ;;
  esac
  echo "false"
}

report_status "Initialization" "Starting control loop for applications/$APPLICATION_NAME..."
previous_healthy="True"
while true; do
  APPLICATION_UID="$(kubectl get "applications/$APPLICATION_NAME" \
    --namespace="$NAMESPACE" \
    --output=jsonpath='{.metadata.uid}')"

  top_level_resources=$(kubectl get "applications/$APPLICATION_NAME" \
      --namespace="$NAMESPACE" \
      --output=json \
    | jq -r '.spec.components[] | to_entries[] | [.value.kind, .key] | join("/")')

  healthy="True"
  for resource in ${top_level_resources[@]}; do
    resource_health=$(is_healthy "$resource")
    if [[ "$resource_health" == "false" ]]; then
      healthy="False"
    fi

    # Note: Updating Services during their provisioning seems to break
    # integrations with GKE, so we delay assigning owner references
    # until resources are healthy.
    if [[ "$resource_health" == "true" ]]; then
      kubectl patch "$resource" \
        --namespace="$NAMESPACE" \
        --type=merge \
        --patch="metadata:
                   ownerReferences:
                   - apiVersion: extensions/v1beta1
                     blockOwnerDeletion: true
                     controller: true
                     kind: Application
                     name: $APPLICATION_NAME
                     uid: $APPLICATION_UID" || true
    fi
  done

  if [[ "$previous_healthy" != "$healthy" ]]; then
    report_status "Initialization" "Found applications/$APPLICATION_NAME ready status to be $healthy."
    kubectl patch "applications/$APPLICATION_NAME" \
      --namespace="$NAMESPACE" \
      --type=merge \
      --patch "metadata:
                 ApplicationStatus:
                   ready: $healthy" || true
    previous_healthy="$healthy"
  fi

  sleep 1
done
