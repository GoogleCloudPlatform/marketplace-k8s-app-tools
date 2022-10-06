FROM marketplace.gcr.io/google/ubuntu2004

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-transport-https \
        bash \
        ca-certificates \
        curl \
        gettext \
        jq \
        make \
        software-properties-common \
        wget \
        gnupg \
        python3 \
        python3-pip \
        python-is-python3 \
     && rm -rf /var/lib/apt/lists/*

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
     && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
     && apt-get -y update \
     && apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin

RUN pip3 install \
      wheel \
      pyOpenSSL \
      pyyaml \
      six

RUN for full_version in 1.21.12 1.22.8 1.23.7;  \
     do \
        version=${full_version%.*} \
        && mkdir -p /opt/kubectl/$version \
        && wget -q -O /opt/kubectl/$version/kubectl \
            https://storage.googleapis.com/kubernetes-release/release/v$full_version/bin/linux/amd64/kubectl \
        && chmod 755 /opt/kubectl/$version/kubectl; \
     done;
RUN ln -s /opt/kubectl/1.22 /opt/kubectl/default

RUN echo "deb [signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu focal edge" | tee /etc/apt/sources.list.d/docker.list \
     && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key --keyring /usr/share/keyrings/docker.gpg add - \
     && apt-get -y update \
     && apt-get -y install docker-ce=5:19.03.13~3-0~ubuntu-focal

RUN mkdir -p /bin/helm-downloaded \
     && wget -q -O /bin/helm-downloaded/helm.tar.gz \
        https://get.helm.sh/helm-v3.9.0-linux-amd64.tar.gz \
     && tar -zxvf /bin/helm-downloaded/helm.tar.gz -C /bin/helm-downloaded \
     && mv /bin/helm-downloaded/linux-amd64/helm /bin/ \
     && rm -rf /bin/helm-downloaded

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
