FROM ubuntu:22.04

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
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
    && rm -rf /var/lib/apt/lists/*

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
     && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
     && apt-get -y update \
     && apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin \
     && rm -rf /var/lib/apt/lists/*

RUN pip3 install \
      wheel \
      pyOpenSSL \
      pyyaml \
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

RUN echo "deb [signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable" | tee /etc/apt/sources.list.d/docker.list \
     && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key --keyring /usr/share/keyrings/docker.gpg add - \
     && apt-get -y update \
     && apt-get -y install docker-ce \
     && rm -rf /var/lib/apt/lists/*

# Install latest stable Helm version using the official script
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
     && chmod 700 get_helm.sh \
     && ./get_helm.sh \
     && rm ./get_helm.sh \
     && echo "Successfully installed Helm:" \
     && helm version

RUN gcloud auth configure-docker

COPY marketplace/deployer_util/* /bin/
COPY scripts/* /scripts/
COPY marketplace/dev/bin/* /bin/
COPY marketplace/dev/fake-reporting-secret-manifest.yaml /data/fake-reporting-secret-manifest.yaml
RUN mv /scripts/doctor.py /scripts/doctor

ENV PATH="/scripts:/bin:/opt/kubectl/default:${PATH}"

RUN mkdir -p /data/

ENTRYPOINT ["/bin/docker_entrypoint.sh"]
CMD ["echo", "It works"]