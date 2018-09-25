ARG BASE_TAG=latest
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$BASE_TAG

ONBUILD COPY chart /tmp/chart.tmp
ONBUILD RUN cd /tmp \
        && mv chart.tmp/* chart \
        && tar -czvf /tmp/chart.tar.gz chart \
        && mkdir -p /data/chart \
        && mv chart.tar.gz /data/chart/ \
        && rm -Rf chart chart.tmp

ONBUILD COPY schema.yaml /data/schema.yaml
# Provide registry prefix and tag for default values for images.
ARG REGISTRY
ARG TAG
ONBUILD RUN cat /data/schema.yaml \
        | env -i "REGISTRY=$REGISTRY" "TAG=$TAG" envsubst \
        > /data/schema.yaml.new \
        && mv /data/schema.yaml.new /data/schema.yaml
