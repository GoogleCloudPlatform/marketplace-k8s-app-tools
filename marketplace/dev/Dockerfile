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

RUN wget -q -O /bin/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
    && chmod 755 /bin/kubectl

RUN wget -q -O /usr/bin/google-cloud-sdk-199.0.0-linux-x86_64.tar.gz \
        https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-199.0.0-linux-x86_64.tar.gz \
    && tar xfC /usr/bin/google-cloud-sdk-199.0.0-linux-x86_64.tar.gz /usr/bin \
    && ln -s /usr/bin/google-cloud-sdk/bin/gcloud /usr/bin/gcloud \
    && chmod 755 /usr/bin/google-cloud-sdk/bin/gcloud

COPY marketplace/deployer_util/* /bin/
COPY scripts/* /scripts/

COPY marketplace/dev/bash_profile /root/.bashrc

ARG SERVICE_ACCOUNT_JSON_FILE
COPY ${SERVICE_ACCOUNT_JSON_FILE} /root/service_account.json
RUN [ -s /root/service_account.json ] \
    && gcloud auth activate-service-account --key-file=/root/service_account.json \
    || >&2 echo 'Skipping service account activation.'


ENTRYPOINT /bin/bash
