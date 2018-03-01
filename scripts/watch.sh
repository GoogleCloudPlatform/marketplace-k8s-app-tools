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

for i in "$@"
do
case $i in
  --name=*)
    name="${i#*=}"
    shift
    ;;
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    ;;
esac
done

[[ -z "$name" ]] && >&2 echo "--name required" && exit 1
[[ -z "$namespace" ]] && >&2 echo "--namespace required" && exit 1

export NAME="$name"
export NAMESPACE="$namespace"

function print_bar() {
  character="$1"
  yes "$character" | tr -d '\n' | head -c$(tput cols)
}
export -f print_bar

function watch_function() {
  # TODO(trironkk): Extract printing and then running a command into a function.
  print_bar =
  echo "Application resources in the following namespace: \"$NAMESPACE\""
  echo "$ kubectl get applications --namespace=\"$NAMESPACE\" --show-kind"
  print_bar -
  echo -e "\n\n"
  kubectl get applications \
      --namespace="$NAMESPACE" \
      --show-kind

  echo -e "\n"
  print_bar =
  echo "Standard resources in the following namespace: \"$NAMESPACE\""
  echo "$ kubectl get all --namespace=\"$NAMESPACE\" --show-kind"
  print_bar -
  echo -e "\n\n"
  kubectl get all \
      --namespace="$NAMESPACE" \
      --show-kind

  echo -e "\n"
  print_bar =
  echo "Events with the following label: app=\"$NAME\""
  echo "$ kubectl get events --namespace="$NAMESPACE" --selector="app=$NAME" \\
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'"
  print_bar -
  echo -e "\n\n"
  kubectl get events --namespace="$NAMESPACE" --selector="app=$NAME" \
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'
}
export -f watch_function

watch --interval 1 --no-title --exec bash -c watch_function
