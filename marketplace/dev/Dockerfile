FROM gcr.io/cloud-builders/docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    gettext \
    jq \
    python \
    python-pip \
    python-setuptools \
    python-yaml \
    wget \
 && rm -rf /var/lib/apt/lists/*

RUN pip install wheel \
 && pip install google-cloud-storage

RUN wget -q -O /bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
 && chmod 755 /bin/kubectl

RUN wget -q -O /usr/bin/google-cloud-sdk-199.0.0-linux-x86_64.tar.gz \
     https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-199.0.0-linux-x86_64.tar.gz \
 && tar xfC /usr/bin/google-cloud-sdk-199.0.0-linux-x86_64.tar.gz /usr/bin \
 && ln -s /usr/bin/google-cloud-sdk/bin/gcloud /usr/bin/gcloud \
 && chmod 755 /usr/bin/google-cloud-sdk/bin/gcloud

COPY marketplace/deployer_util/* /bin/
COPY scripts/* /scripts/
COPY scripts/driver/* /scripts/driver/
COPY marketplace/dev/mount_kubeconfig.sh /bin/mount_kubeconfig.sh
RUN mkdir -p /data/

ENTRYPOINT ["/bin/bash", "-x"]
