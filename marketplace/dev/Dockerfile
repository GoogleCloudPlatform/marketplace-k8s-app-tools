FROM launcher.gcr.io/google/ubuntu16_04

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-transport-https \
        bash \
        ca-certificates \
        curl \
        curl \
        gettext \
        jq \
        make \
        python \
        python-pip \
        python-setuptools \
        python-yaml \
        software-properties-common \
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

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    apt-key fingerprint 0EBFCD88 && \
    add-apt-repository \
       "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
       xenial \
       edge" && \
    apt-get -y update && \
    apt-get -y install docker-ce=17.12.0~ce-0~ubuntu

COPY marketplace/deployer_util/* /bin/
COPY scripts/* /scripts/
COPY marketplace/dev/setup_kubeconfig.sh /bin/setup_kubeconfig.sh
RUN mkdir -p /data/

ENTRYPOINT ["/bin/bash"]
