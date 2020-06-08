ARG FROM=gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:latest
FROM $FROM

ONBUILD COPY manifest /data/manifest
ONBUILD COPY schema.yaml /data/schema.yaml
# Provide registry prefix and tag for default values for images.
ONBUILD ARG REGISTRY
ONBUILD ARG TAG
ONBUILD RUN cat /data/schema.yaml \
        | env -i "REGISTRY=$REGISTRY" "TAG=$TAG" envsubst \
        > /data/schema.yaml.new \
        && mv /data/schema.yaml.new /data/schema.yaml
