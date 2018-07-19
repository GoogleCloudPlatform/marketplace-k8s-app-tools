#!/bin/bash

# If ~/mount/.kube/ exists ($KUBECONFIG is mounted) and ~/.kube does not
# (we have not yet initialized), copy system kubectl configuration to
# them to the default $KUBECONFIG location after adjusting system-specific
# fields.
if [[ -e "/root/mount/.kube/config" && ! -e "/root/.kube/config" ]]; then
  mkdir -p /root/.kube

  cat /root/mount/.kube/config \
    | yaml2json \
    | jq \
          --arg gcloud "$(readlink -f "$(which gcloud)")" \
          '.users = [ .users[] |
                      if .user["auth-provider"]["name"] == "gcp"
                        then .user["auth-provider"]["config"]["cmd-path"] = $gcloud
                        else .
                      end
                    ]' \
  > /root/.kube/config
fi
