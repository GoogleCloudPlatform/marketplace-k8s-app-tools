FROM marketplace.gcr.io/google/python

# Add the Cloud SDK distribution URI as a package source
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
# Import the Google Cloud Platform public key
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-transport-https \
        bash \
        ca-certificates \
        curl \
        gettext \
        google-cloud-sdk \
        jq \
        make \
        software-properties-common \
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
COPY marketplace/dev/fake-reporting-secret-manifest.yaml /data/fake-reporting-secret-manifest.yaml
RUN mv /scripts/doctor.py /scripts/doctor

ENV PATH="/scripts:/bin:${PATH}"

RUN mkdir -p /data/

ENTRYPOINT ["/bin/docker_entrypoint.sh"]
CMD ["echo", "It works"]
