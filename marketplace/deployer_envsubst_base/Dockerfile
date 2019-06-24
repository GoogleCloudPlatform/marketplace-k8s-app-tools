FROM launcher.gcr.io/google/debian9

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    gettext \
    jq \
    python \
    python-openssl \
    python-pip \
    python-setuptools \
    python-yaml \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O /bin/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.13.2/bin/linux/amd64/kubectl \
    && chmod 755 /bin/kubectl

COPY marketplace/deployer_envsubst_base/* /bin/
COPY marketplace/deployer_util/* /bin/
ARG VERSION
RUN echo "$VERSION" > /version

RUN mkdir -p /data/manifest

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
