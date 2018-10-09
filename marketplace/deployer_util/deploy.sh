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

INGRESS_IP=127.0.0.1

set -eox pipefail

get_domain_name() {
  echo "$NAME.$INGRESS_IP.xip.io"
}

# Installs CloudBees Jenkins Enterprise
install_cje() {
    local source=${1:?}
    local install_file; install_file=$(mktemp)
    cp $source $install_file
    
    # Set domain
    sed -i -e "s#cje.example.com#$(get_domain_name)#" "$install_file"
    kubectl apply -f "$install_file"
}

# Installs ingress controller
install_ingress_controller() {
    if [[ -z $(kubectl get svc | grep $NAME-ingress-nginx ) ]]; then
      local source=${1:?}
      local install_file; install_file=$(mktemp)
      cp $source $install_file
      kubectl apply -f "$install_file"
      echo "Installed ingress controller."
    else
      echo "Ingress controller already exists."
    fi
    
    
    while [[ "$(kubectl get svc $NAME-ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')" = '' ]]; do sleep 3; done
    INGRESS_IP=$(kubectl get svc $NAME-ingress-nginx  -o jsonpath='{.status.loadBalancer.ingress[0].ip}' | sed 's/"//g')
    echo "NGINX INGRESS: $INGRESS_IP"
}

#create self-signed cert
create_cert(){
  local source=/data/server.config
  local config_file; config_file=$(mktemp)
  cp $source $config_file

  sed -i -e "s#cje.example.com#$(get_domain_name)#" "$config_file"

  openssl req -config "$config_file" -new -newkey rsa:2048 -nodes -keyout server.key -out server.csr

  echo "Created server.key"
  echo "Created server.csr"

  openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
  echo "Created server.crt (self-signed)"

  kubectl create secret tls $NAME-tls --cert=server.crt --key=server.key
}

# This is the entry point for the production deployment

# If any command returns with non-zero exit code, set -e will cause the script
# to exit. Prior to exit, set App assembly status to "Failed".
handle_failure() {
  code=$?
  if [[ -z "$NAME" ]] || [[ -z "$NAMESPACE" ]]; then
    # /bin/expand_config.py might have failed.
    # We fall back to the unexpanded params to get the name and namespace.
    NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}' \
            --values_file /data/values.yaml --values_dir /data/values)"
    NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}' \
                 --values_file /data/values.yaml --values_dir /data/values)"
    export NAME
    export NAMESPACE
  fi
  patch_assembly_phase.sh --status="Failed"
  exit $code
}
trap "handle_failure" EXIT

/bin/expand_config.py
NAME="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAME"}}')"
NAMESPACE="$(/bin/print_config.py --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')"
export NAME
export NAMESPACE

echo "Deploying application \"$NAME\""

app_uid=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.metadata.uid}')
app_api_version=$(kubectl get "applications/$NAME" \
  --namespace="$NAMESPACE" \
  --output=jsonpath='{.apiVersion}')

create_manifests.sh

install_ingress_controller "/data/manifest-ingress-expanded/nginx.yaml"

###cje###
# Assign owner references for the resources.
/bin/set_ownership.py \
  --app_name "$NAME" \
  --app_uid "$app_uid" \
  --app_api_version "$app_api_version" \
  --manifests "/data/manifest-expanded" \
  --dest "/data/cje.yaml"

# Ensure assembly phase is "Pending", until successful kubectl apply.
/bin/setassemblyphase.py \
  --manifest "/data/cje.yaml" \
  --status "Pending"

#generate a self-signed cert
create_cert

install_cje "/data/cje.yaml"

sleep 20

kubectl create secret generic initialAdminPassword --from-literal=password=$(kubectl exec $NAME-cjoc-0 -n $NAMESPACE -- cat /var/jenkins_home/secrets/initialAdminPassword)

patch_assembly_phase.sh --status="Success"

clean_iam_resources.sh

echo "CloudBees Jenkins Enterprise is installed and running at http://$(get_domain_name)/cjoc."

trap - EXIT
