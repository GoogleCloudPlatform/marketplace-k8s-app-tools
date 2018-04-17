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

set -x
set -e
set -o pipefail

app=$1
namespace=$2

function is_healthy() {
  resource="$1"
  kind=${resource%/*}
  name=${resource#*/}
  case "$kind" in
    Deployment)
      ready_replicas=$(kubectl get "deployments/$name" \
          --namespace="$namespace" \
          --output=jsonpath='{.status.readyReplicas}')
      total_replicas=$(kubectl get "deployments/$name" \
          --namespace="$namespace" \
          --output=jsonpath='{.spec.replicas}')
      if [[ "$ready_replicas" == "$total_replicas" ]]; then
        echo "true"; return
      fi
      ;;
    PersistentVolumeClaim)
      phase=$(kubectl get "persistentvolumeclaims/$name" \
          --namespace="$namespace" \
          --output=jsonpath='{.status.phase}')
      if [[ "$phase" == "Bound" ]]; then
        echo "true"; return
      fi
      ;;
    Service)
      service_type=$(kubectl get "services/$name" \
          --namespace="$namespace" \
          --output=jsonpath='{.spec.type}')
      if [[ "$service_type" != "LoadBalancer" ]]; then
        echo "true"; return
      fi
      service_ip=$(kubectl get "services/$name" \
          --namespace="$namespace" \
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

echo "INFO Starting control loop for applications/$app..."
previous_healthy="True"

total_time=0
healthy_time=0
healthy_time_target=10
poll_interval=4

while true; do
  APPLICATION_UID="$(kubectl get "applications/$app" \
    --namespace="$namespace" \
    --output=jsonpath='{.metadata.uid}')"

  top_level_kinds=$(kubectl get "applications/$app" \
    --namespace="$namespace" \
    --output=json \
    | jq -r '.spec.componentKinds[] | .kind')

  top_level_resources=()
  for kind in ${top_level_kinds[@]}; do
    top_level_resources+=($(kubectl get "$kind" \
      --namespace="$namespace" \
      --selector app.kubernetes.io/name="$app" \
      --output=json \
      | jq -r '.items[] | [.kind, .metadata.name] | join("/")'))
  done

  echo "INFO top level resources: ${#top_level_resources[@]}"
  if [[ "${#top_level_resources[@]}" = "0" ]]; then
    echo "ERROR no top level resources found"
    exit 1
  fi

  healthy="True"
  for resource in ${top_level_resources[@]}; do
    resource_health=$(is_healthy "$resource")
    if [[ "$resource_health" == "false" ]]; then
      healthy="False"
      break
    fi
  done

  if [[ "$previous_healthy" != "$healthy" ]]; then
    echo "INFO Initialization" "Found applications/$app ready status to be $healthy."
    previous_healthy="$healthy"
  fi

  total_time=$((total_time+poll_interval))
  if [[ "$healthy" = "True" ]]; then
    healthy_time=$((healthy_time+poll_interval))
    if [[ $healthy_time -ge $healthy_time_target ]];then 
      exit 0
    fi
  fi
  sleep $poll_interval
done
