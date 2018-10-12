ARG MARKETPLACE_TOOLS_TAG
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$MARKETPLACE_TOOLS_TAG

COPY schema.yaml /data

COPY chartmuseum-marketplace /tmp/chartmuseum-marketplace

RUN mkdir -p /data/chart \
 && cd /data/chart \
 && helm dependency build /tmp/chartmuseum-marketplace \
 && find /tmp/chartmuseum-marketplace \
 && helm package /tmp/chartmuseum-marketplace \
 && rm -rf /tmp/chartmuseum-marketplace
