FROM gcr.io/cloud-builders/gcloud

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-transport-https \
        bash \
        ca-certificates \
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

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    apt-key fingerprint 0EBFCD88 && \
    add-apt-repository \
       "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
       xenial \
       edge" && \
    apt-get -y update && \
    apt-get -y install docker-ce=17.12.0~ce-0~ubuntu

RUN mkdir -p /bin/helm-downloaded \
     && wget -q -O /bin/helm-downloaded/helm.tar.gz \
        https://storage.googleapis.com/kubernetes-helm/helm-v2.10.0-linux-amd64.tar.gz \
     && tar -zxvf /bin/helm-downloaded/helm.tar.gz -C /bin/helm-downloaded \
     && mv /bin/helm-downloaded/linux-amd64/helm /bin/ \
     && rm -rf /bin/helm-downloaded \
     && helm init --client-only

RUN gcloud auth configure-docker

COPY marketplace/deployer_util/* /bin/
COPY scripts/* /scripts/
COPY marketplace/dev/bin/* /bin/
RUN mkdir -p /data/

ENTRYPOINT ["/bin/docker_entrypoint.sh"]
CMD ["echo", "It works"]
