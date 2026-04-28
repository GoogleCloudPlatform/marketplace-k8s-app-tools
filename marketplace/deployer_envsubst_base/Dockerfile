FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    gettext \
    jq \
    wget \
    python3 \
    python3-pip \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install \
      wheel \
      pyOpenSSL \
      pyyaml \
      six \
      cryptography>=46.0.7

# Download the latest stable version of kubectl
RUN LATEST_STABLE=$(curl -L -s https://dl.k8s.io/release/stable.txt) \
    && echo "Attempting to download kubectl version: $LATEST_STABLE" \
    && VERSION_MAJOR=$(echo $LATEST_STABLE | cut -d. -f1-2) \
    && mkdir -p /opt/kubectl/$VERSION_MAJOR \
    && wget -q -O /opt/kubectl/$VERSION_MAJOR/kubectl \
        https://dl.k8s.io/release/$LATEST_STABLE/bin/linux/amd64/kubectl \
    && chmod 755 /opt/kubectl/$VERSION_MAJOR/kubectl \
    && ln -sfn /opt/kubectl/$VERSION_MAJOR /opt/kubectl/default \
    && echo "Successfully installed kubectl $LATEST_STABLE" \
    && /opt/kubectl/default/kubectl version --client

# Add kubectl to the PATH
ENV PATH="/opt/kubectl/default:${PATH}"

COPY marketplace/deployer_envsubst_base/* /bin/
COPY marketplace/deployer_util/* /bin/
ARG VERSION
RUN echo "$VERSION" > /version

RUN mkdir -p /data/manifest

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]