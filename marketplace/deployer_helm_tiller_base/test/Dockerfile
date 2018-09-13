ARG MARKETPLACE_TOOLS_TAG
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$MARKETPLACE_TOOLS_TAG

COPY marketplace/deployer_helm_tiller_base/test/schema.yaml /data

COPY marketplace/deployer_helm_tiller_base/test/chartmuseum /tmp/chartmuseum
COPY marketplace/deployer_helm_tiller_base/test/application.yaml /tmp/chartmuseum/templates
COPY marketplace/deployer_helm_tiller_base/test/post-install.yaml /tmp/chartmuseum/templates
COPY marketplace/deployer_helm_tiller_base/test/post-delete.yaml /tmp/chartmuseum/templates

RUN mkdir -p /data/chart \
 && cd /data/chart \
 && helm package /tmp/chartmuseum \
 && rm -rf /tmp/chartmuseum
