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

for i in "$@"
do
case $i in
  --tester_img=*)
    tester_img="${i#*=}"
    shift
    ;;
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  *)
    echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$tester_img" ]] && echo "tester_img required" && exit 1
[[ -z "$namespace" ]] && echo "namespace required" && exit 1

echo $tester_img

# Create dummy tester.
kubectl create --namespace="$namespace" --filename=- <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: "tester"
  labels:
    app.kubernetes.io/name: "tester"
    tester: "true"
spec:
  template:
    spec:
      containers:
      - name: app
        image: "$tester_img"
        env:
        - name: EXITCODE
          value: "0"
        - name: DURATION
          value: "20"
      restartPolicy: Never
  backoffLimit: 0
EOF