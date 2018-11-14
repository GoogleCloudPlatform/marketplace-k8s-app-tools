FROM gcr.io/cloud-builders/gcloud-slim

ARG VERSION
ENV VERSION $VERSION

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        git \
        wget \
     && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /bin/helm-downloaded \
     && wget -q -O /bin/helm-downloaded/helm.tar.gz \
        https://storage.googleapis.com/kubernetes-helm/helm-v2.10.0-linux-amd64.tar.gz \
     && tar -zxvf /bin/helm-downloaded/helm.tar.gz -C /bin/helm-downloaded \
     && mv /bin/helm-downloaded/linux-amd64/helm /bin/ \
     && rm -rf /bin/helm-downloaded \
     && helm init --client-only

COPY . /charts

RUN find /charts \
    && echo VERSION="$VERSION" \
    && mkdir /charts-tgz/ \
    && helm package /charts/marketplace-integration/ \
           --version "$VERSION" \
           --destination /charts-tgz/

#     && gsutil cp "/charts-tgz/marketplace-integration-$VERSION.tgz" "gs://$CHART_BUCKET/" \
#     && helm repo index \
#            --url "https://$CHART_BUCKET.storage.googleapis.com" \
#            --merge /tmp/index.yaml \
#            /charts-tgz/ \
#     && gsutil cp /charts-tgz/index.yaml "gs://$CHART_BUCKET/index.yaml"
