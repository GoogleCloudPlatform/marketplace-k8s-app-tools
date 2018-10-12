ARG MARKETPLACE_TOOLS_TAG
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$MARKETPLACE_TOOLS_TAG

COPY schema.yaml /data

COPY chartmuseum-marketplace /tmp/chartmuseum-marketplace

RUN mkdir -p /data/chart \
 && cd /data/chart \
 && helm package --dependency-update /tmp/chartmuseum-marketplace --destination /data/chart/ \
 && find /tmp/chartmuseum-marketplace \
 && rm -rf /tmp/chartmuseum-marketplace
