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
  --name=*)
    name="${i#*=}"
    shift
    ;;
  --namespace=*)
    namespace="${i#*=}"
    shift
    ;;
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  --parameters=*)
    parameters="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$name" ]] && >&2 echo "--name required" && exit 1
[[ -z "$namespace" ]] && namespace="default"
[[ -z "$deployer" ]] && >&2 echo "--deployer required" && exit 1
[[ -z "$parameters" ]] && parameters="{}"

# Create Application instance.
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: app.k8s.io/v1alpha1
kind: Application
metadata:
  name: "${name}"
  namespace: "${namespace}"
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: "${name}"
  componentKinds:
  - kind: ServiceAccount
  - kind: RoleBinding
  - kind: Job
EOF

# Create Application instance.
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: app.k8s.io/v1alpha1
kind: Application
metadata:
  name: "${name}"
  namespace: "${namespace}"
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: "${name}"
  componentKinds:
  - kind: ServiceAccount
  - kind: RoleBinding
  - kind: Job
EOF

# Create RBAC role, service account, and role-binding.
# TODO(huyhuynh): Application should define the desired permissions,
# which should be transated into appropriate rules here instead of
# granting the role with all permissions.
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: "${name}-deployer-sa"
  namespace: "${namespace}"
  labels:
    app.kubernetes.io/name: "${name}"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: "${name}-deployer-rb"
  namespace: "${namespace}"
  labels:
    app.kubernetes.io/name: "${name}"
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: "${name}-deployer-sa"
EOF

# Create ConfigMap (merging in passed in parameters).
kubectl apply --filename=- --output=json --dry-run <<EOF \
  | jq -s '.[0].data += .[1] | .[0]' \
      - <(echo "$parameters") \
  | kubectl apply --namespace="$namespace" --filename=-
apiVersion: v1
kind: ConfigMap
metadata:
  name: "${name}-deployer-config"
  namespace: "${namespace}"
data:
  APP_INSTANCE_NAME: ${name}
  NAMESPACE: ${namespace}
EOF

# Create deployer.
kubectl apply --namespace="$namespace" --filename=- <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: "${name}-deployer"
  labels:
    app.kubernetes.io/name: "${name}"
spec:
  template:
    spec:
      serviceAccountName: "${name}-deployer-sa"
      containers:
      - name: app
        image: "${deployer}"
        envFrom:
        - configMapRef:
            name: "${name}-deployer-config"
      restartPolicy: Never
EOF
