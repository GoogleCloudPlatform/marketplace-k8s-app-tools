#!/bin/bash

# If host kubernetes configuration is mounted, copy it to the container's
# default $KUBECONFIG location after adjusting system-specific fields.
if [[ -e "/root/mount/.kube/config" ]]; then
  mkdir -p "$HOME/.kube"

  # Adjusting cmd-path for gcp auth-providers to this container's gcloud
  # installation location.
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
  > "$HOME/.kube/config"
fi

# If host gcloud configuration is mounted, replace container gcloud
# configuration with it.
# Note: We do this to ensure the directory is writable without providing
# write access to host gcloud configuration directory.
if [[ -e "/root/mount/.config/gcloud" ]]; then
  rm -rf "$HOME/.config/gcloud"
  cp -r "/root/mount/.config/gcloud" "$HOME/.config"
fi
