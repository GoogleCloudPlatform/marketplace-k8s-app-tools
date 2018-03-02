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
set -o pipefail

for i in "$@"
do
case $i in
  --app-name=*)
    app_name="${i#*=}"
    shift
    ;;
  --name=*)
    name="${i#*=}"
    shift
    ;;
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  --registry=*)
    registry="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$app_name" ]] && >&2 echo "--app-name required" && exit 1
[[ -z "$name" ]] && name="$app_name"-1
[[ -z "$namespace" ]] && namespace="default"
[[ -z "$registry" ]] && >&2 echo "--registry required" && exit 1

# Create RBAC role, service account, and role-binding.
# TODO(huyhuynh): Application should define the desired permissions,
# which should be transated into appropriate rules here instead of
# granting the role with all permissions.
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${name}-deployer-sa
  namespace: $namespace
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ${name}-deployer-role
  namespace: $namespace
rules:
- apiGroups: ['*']
  resources: ['*']
  verbs: ['*']
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${name}-deployer-rb
  namespace: $namespace
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ${name}-deployer-role
subjects:
- kind: ServiceAccount
  name: ${name}-deployer-sa
EOF

# Create Application instance (stitching in the expanded manifest).
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: marketplace.cloud.google.com/v1
kind: Application
metadata:
  name: $name
  namespace: $namespace
spec:
  components:
  - ${name}-deployer-sa:
      kind: ServiceAccount
  - ${name}-deployer-role:
      apiGroup: rbac.authorization.k8s.io
      kind: Role
  - ${name}-deployer-rb:
      apiGroup: rbac.authorization.k8s.io
      kind: RoleBinding
  - ${name}-deployer:
      kind: Job
EOF

# Create deployer.
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: "${name}-deployer"
spec:
  template:
    spec:
      serviceAccountName: ${name}-deployer-sa
      containers:
      - name: app
        image: "$registry/$app_name/deployer"
        env:
        - name: APPLICATION_NAME
          value: "$name"
        - name: NAMESPACE
          value: "$namespace"
        - name: REGISTRY
          value: "$registry"
      restartPolicy: Never
EOF
