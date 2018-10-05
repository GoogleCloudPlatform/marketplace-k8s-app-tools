ARG MARKETPLACE_TOOLS_TAG
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$MARKETPLACE_TOOLS_TAG

COPY marketplace/deployer_helm_tiller_base/test/schema.yaml /data

COPY marketplace/deployer_helm_tiller_base/test/chartmuseum-marketplace /tmp/chartmuseum-marketplace

RUN mkdir -p /data/chart \
 && cd /data/chart \
 && helm dependency build /tmp/chartmuseum-marketplace \
 && find /tmp/chartmuseum-marketplace \
 && helm package /tmp/chartmuseum-marketplace \
 && rm -rf /tmp/chartmuseum-marketplace
