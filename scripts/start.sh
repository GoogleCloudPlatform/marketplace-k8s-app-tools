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
  --deployer=*)
    deployer="${i#*=}"
    shift
    ;;
  --parameters=*)
    parameters="${i#*=}"
    shift
    ;;
  --entrypoint=*)
    entrypoint="${i#*=}"
    shift
    ;;
  *)
    >&2 echo "Unrecognized flag: $i"
    exit 1
    ;;
esac
done

[[ -z "$deployer" ]] && >&2 echo "--deployer required" && exit 1
[[ -z "$parameters" ]] && >&2 echo "--parameters required" && exit 1
[[ -z "$entrypoint" ]] && entrypoint="/bin/deploy.sh"

name="$( \
  echo "${parameters}" \
  | docker run -i --entrypoint=/bin/print_config.py --rm "${deployer}" \
    --values_file=- --param '{"x-google-marketplace": {"type": "NAME"}}')"
namespace="$( \
  echo "${parameters}"\
  | docker run -i --entrypoint=/bin/print_config.py --rm "${deployer}" \
    --values_file=- --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"

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
  assemblyPhase: "Pending"
EOF

app_uid=$(kubectl get "applications/$name" \
  --namespace="$namespace" \
  --output=jsonpath='{.metadata.uid}')
app_api_version=$(kubectl get "applications/$name" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.apiVersion}')

# Provisions external resource dependencies and the deployer resources.
# We set the application as the owner for all of these resources.
echo "${parameters}" \
  | docker run -i --entrypoint=/bin/provision.py --rm "${deployer}" \
    --values_file=- --deployer_image="${deployer}" --deployer_entrypoint="${entrypoint}" \
  | docker run -i --entrypoint=/bin/set_app_labels.py --rm "${deployer}" \
    --manifests=- --dest=- --name="${name}" --namespace="${namespace}" \
  | docker run -i --entrypoint=/bin/set_ownership.py --rm "${deployer}" \
    --manifests=- --dest=- --noapp \
    --app_name="${name}" --app_uid="${app_uid}" --app_api_version="${app_api_version}" \
  | kubectl apply --namespace="$namespace" --filename=-
