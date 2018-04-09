FROM launcher.gcr.io/google/debian9

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*
RUN wget -q -O /bin/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
    && chmod 755 /bin/kubectl
RUN mkdir -p /bin/helm-downloaded \
    && wget -q -O /bin/helm-downloaded/helm.tar.gz \
        https://storage.googleapis.com/kubernetes-helm/helm-v2.8.1-linux-amd64.tar.gz \
    && tar -zxvf /bin/helm-downloaded/helm.tar.gz -C /bin/helm-downloaded \
    && mv /bin/helm-downloaded/linux-amd64/helm /bin/ \
    && rm -rf /bin/helm-downloaded
RUN apt-get update \
    && apt-get install -y --no-install-recommends apt-utils bash gettext jq
RUN apt-get update \
    && apt-get install -y --no-install-recommends python
RUN apt-get update \
    && apt-get install -y --no-install-recommends python-yaml

COPY marketplace/deployer_helm_base/deploy.sh /bin/
COPY marketplace/deployer_util/setownership.py /bin/
COPY marketplace/deployer_util/util.py /bin/

RUN mkdir -p /data/chart

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
