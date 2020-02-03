#!/bin/bash

set -euo pipefail

# KUBE_CONFIG can point to a kubeconfig file or
# the standard kubectl config directory.
KUBE_CONFIG=${KUBE_CONFIG:-$HOME/.kube/config}
GCLOUD_CONFIG=${GCLOUD_CONFIG:-$HOME/.config/gcloud}
EXTRA_DOCKER_PARAMS=${EXTRA_DOCKER_PARAMS:-}
MARKETPLACE_TOOLS_TAG=${MARKETPLACE_TOOLS_TAG:-latest}
MARKETPLACE_TOOLS_IMAGE=${MARKETPLACE_TOOLS_IMAGE:-gcr.io/cloud-marketplace-tools/k8s/dev}

kube_mount=""
if [[ -f "${KUBE_CONFIG}" ]]; then
  # Mount as a file.
  kube_mount=(--mount "type=bind,source=${KUBE_CONFIG},target=/mount/config/.kube/config,readonly")
elif [[ -d "${KUBE_CONFIG}" ]]; then
  # Mount as a directory.
  kube_mount=(--mount "type=bind,source=${KUBE_CONFIG},target=/mount/config/.kube,readonly")
fi

gcloud_mount=""
# gcloud_original_path is used for determining the prefix to filenames referenced
# by certain config files. Such prefix must be replaced by the corresponding
# mount path in the container.
gcloud_original_path=""
if [[ -e "${GCLOUD_CONFIG}" ]]; then
  gcloud_mount=(--mount "type=bind,source=${GCLOUD_CONFIG},target=/mount/config/.config/gcloud,readonly")
  # Note: readlink -f doesn't work on non-GNU so we would fallback to python in that case.
  canonical_gcloud_config="$( \
    readlink -f "${GCLOUD_CONFIG}" 2> /dev/null \
    || python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "${GCLOUD_CONFIG}" \
  )"
  gcloud_original_path=(--env "GCLOUD_ORIGINAL_PATH=${canonical_gcloud_config}")
fi

terminal_docker_param="-t"
if [[ -t 0 ]]; then
  terminal_docker_param="-it"
fi

docker run \
  --mount "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,readonly" \
  --net=host \
  ${kube_mount[*]} \
  ${gcloud_mount[*]} \
  ${gcloud_original_path[*]} \
  ${EXTRA_DOCKER_PARAMS[*]} \
  "${terminal_docker_param}" --rm \
  "${MARKETPLACE_TOOLS_IMAGE}:${MARKETPLACE_TOOLS_TAG}" \
  "$@"
