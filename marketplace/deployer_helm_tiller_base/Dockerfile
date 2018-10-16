FROM launcher.gcr.io/google/debian9

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    gettext \
    git \
    jq \
    procps \
    python \
    python-pip \
    python-setuptools \
    python-yaml \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install wheel \
    && pip install google-cloud-storage

RUN wget -q -O /bin/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
    && chmod 755 /bin/kubectl

RUN mkdir -p /bin/helm-downloaded \
    && wget -q -O /bin/helm-downloaded/helm.tar.gz \
        https://storage.googleapis.com/kubernetes-helm/helm-v2.10.0-linux-amd64.tar.gz \
    && tar -zxvf /bin/helm-downloaded/helm.tar.gz -C /bin/helm-downloaded \
    && mv /bin/helm-downloaded/linux-amd64/helm /bin/ \
    && rm -rf /bin/helm-downloaded \
    && helm init --client-only \
    && helm plugin install https://github.com/rimusz/helm-tiller \
    && helm repo add cloud-marketplace-tools-charts https://cloud-marketplace-tools-charts.storage.googleapis.com

COPY marketplace/deployer_util/* /bin/
COPY marketplace/deployer_helm_tiller_base/bin/* /bin/

RUN mkdir -p /data/chart

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]

ONBUILD COPY . /tmp/onbuild

ONBUILD ARG HELM_DEPENDENCY_BUILD=false
ONBUILD ENV HELM_DEPENDENCY_BUILD $HELM_DEPENDENCY_BUILD

# Partner directory structure assertions.
ONBUILD RUN if [ "$(find /tmp/onbuild/chart -maxdepth 1 -mindepth 1 -type d -printf '\n' | wc -l)" -ne 1 ]; then \
              >&2 echo "Too many charts in chart/." ; \
              find /tmp/onbuild ; \
              exit 1 ; \
            fi ; \
            if [ ! -f /tmp/onbuild/schema.yaml ]; then \
              >&2 echo "Missing schema.yaml." ; \
              find /tmp/onbuild ; \
              exit 1 ; \
            fi

ONBUILD RUN export CHART_NAME="$(find /tmp/onbuild/chart -maxdepth 1 -mindepth 1 -type d -printf '%P\n')" \
            && cp /tmp/onbuild/schema.yaml /data/schema.yaml \
            && mkdir -p /data/chart \
            && cd /data/chart \
            && if [ "$HELM_DEPENDENCY_BUILD" = "true" ]; then \
                 helm dependency update "/tmp/onbuild/chart/$CHART_NAME" ; \
               fi \
            && helm package "/tmp/onbuild/chart/$CHART_NAME" --destination /data/chart/ \
            && rm -rf /tmp/onbuild
