FROM marketplace.gcr.io/google/python

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    gettext \
    jq \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install \
      wheel \
      pyOpenSSL \
      pyyaml \
      six

RUN mkdir -p /opt/kubectl/1.13 \
    && wget -q -O /opt/kubectl/1.13/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.13.12/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/1.13/kubectl
RUN mkdir -p /opt/kubectl/1.14 \
    && wget -q -O /opt/kubectl/1.14/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.14.8/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/1.14/kubectl
RUN mkdir -p /opt/kubectl/1.15 \
    && wget -q -O /opt/kubectl/1.15/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.15.11/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/1.15/kubectl
RUN mkdir -p /opt/kubectl/1.16 \
    && wget -q -O /opt/kubectl/1.16/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.16.9/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/1.16/kubectl
RUN mkdir -p /opt/kubectl/1.17 \
    && wget -q -O /opt/kubectl/1.17/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.17.5/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/1.17/kubectl
RUN mkdir -p /opt/kubectl/1.18 \
    && wget -q -O /opt/kubectl/1.18/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.18.2/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/1.18/kubectl
RUN ln -s /opt/kubectl/1.14 /opt/kubectl/default

COPY marketplace/deployer_envsubst_base/* /bin/
COPY marketplace/deployer_util/* /bin/
ARG VERSION
RUN echo "$VERSION" > /version

RUN mkdir -p /data/manifest

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
