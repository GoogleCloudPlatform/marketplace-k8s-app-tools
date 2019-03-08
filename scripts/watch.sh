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

set -eo pipefail

for i in "$@"
do
case $i in
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$namespace" ]] && >&2 echo "--namespace required" && exit 1
export namespace

function print_bar() {
  character="$1"
  yes "$character" | tr -d '\n' | head -c$(tput cols)
}
export -f print_bar

function watch_function() {
  # TODO(trironkk): Extract printing and then running a command into a function.
  print_bar =
  echo "Application resources in the following namespace: \"$namespace\""
  echo "$ kubectl get applications.app.k8s.io --namespace=\"$namespace\" --show-kind"
  print_bar -
  kubectl get applications.app.k8s.io \
      --namespace="$namespace" \
      --show-kind

  echo
  print_bar =
  echo "Standard resources in the following namespace: \"$namespace\""
  echo "$ kubectl get all --namespace=\"$namespace\" --show-kind"
  print_bar -
  kubectl get all \
      --namespace="$namespace" \
      --show-kind

  echo
  print_bar =
  echo "Service accounts and roles in the following namespace: \"$namespace\""
  echo "$ kubectl get serviceaccounts,roles,rolebindings,PersistentVolumeClaims,configmap --namespace=\"$namespace\" --show-kind"
  print_bar -
  kubectl get serviceaccounts,roles,rolebindings,PersistentVolumeClaims,configmap \
      --namespace="$namespace" \
      --show-kind

  echo
  print_bar =
  echo "Events in the namespace"
  echo "$ kubectl get events --namespace="$namespace" \
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'"
  print_bar -
  kubectl get events --namespace="$namespace" \
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'
}
export -f watch_function

watch --interval 1 --no-title --exec bash -c watch_function
