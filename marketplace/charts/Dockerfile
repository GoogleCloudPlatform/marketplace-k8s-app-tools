FROM gcr.io/cloud-builders/gcloud-slim

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
     && helm init --client-only \
     && helm plugin install https://github.com/rimusz/helm-tiller \
     && helm repo add cloud-marketplace-tools https://cloud-marketplace-tools-charts.storage.googleapis.com

COPY . /charts

RUN export VERSION=0.0.1 ; find /charts \
    && mkdir /charts-tgz/ \
    && helm package /charts/marketplace-hooks/ \
      --version $VERSION \
      --destination /charts-tgz/ \
    && gsutil cp /charts-tgz/marketplace-hooks-$VERSION.tgz gs://cloud-marketplace-tools-charts/ \
    && helm repo index \
      --url https://cloud-marketplace-tools-charts.storage.googleapis.com \
      --merge ~/.helm/repository/cache/cloud-marketplace-tools-index.yaml \
      /charts-tgz/ \
    && gsutil cp /charts-tgz/index.yaml gs://cloud-marketplace-tools-charts/index.yaml
