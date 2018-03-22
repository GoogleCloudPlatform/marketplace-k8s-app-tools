FROM launcher.gcr.io/google/debian9

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*
RUN wget -q -O /bin/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
    && chmod 755 /bin/kubectl
COPY marketplace/deployer_kubectl_base/deploy.sh /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash gettext jq

RUN mkdir -p /data/manifest

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
