ARG MARKETPLACE_TOOLS_TAG
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$MARKETPLACE_TOOLS_TAG

COPY marketplace/deployer_helm_tiller_base/test/schema.yaml /data

COPY marketplace/deployer_helm_tiller_base/test/nginx-ingress /tmp/nginx-ingress
COPY marketplace/deployer_helm_tiller_base/test/application.yaml /tmp/nginx-ingress/templates
COPY marketplace/deployer_helm_tiller_base/test/post-install.yaml /tmp/nginx-ingress/templates

RUN mkdir -p /data/chart \
 && cd /data/chart \
 && helm package /tmp/nginx-ingress \
 && rm -rf /tmp/nginx-ingress
