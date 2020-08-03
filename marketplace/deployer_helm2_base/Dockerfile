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

RUN for full_version in 1.13.12 1.14.8 1.15.11 1.16.9 1.17.5 1.18.2;  \
     do \
        version=${full_version%.*} \
        && mkdir -p /opt/kubectl/$version \
        && wget -q -O /opt/kubectl/$version/kubectl \
            https://storage.googleapis.com/kubernetes-release/release/v$full_version/bin/linux/amd64/kubectl \
        && chmod 755 /opt/kubectl/$version/kubectl; \
     done;
RUN ln -s /opt/kubectl/1.16 /opt/kubectl/default

RUN mkdir -p /bin/helm-downloaded \
    && wget -q -O /bin/helm-downloaded/helm.tar.gz \
        https://get.helm.sh/helm-v2.16.9-linux-amd64.tar.gz \
    && tar -zxvf /bin/helm-downloaded/helm.tar.gz -C /bin/helm-downloaded \
    && mv /bin/helm-downloaded/linux-amd64/helm /bin/ \
    && rm -rf /bin/helm-downloaded

COPY marketplace/deployer_helm2_base/* /bin/
COPY marketplace/deployer_util/* /bin/
ARG VERSION
RUN echo "$VERSION" > /version

RUN mkdir -p /data/chart
RUN mkdir -p /data-test/chart

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
