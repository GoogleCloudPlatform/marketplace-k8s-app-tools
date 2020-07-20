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

COPY marketplace/deployer_envsubst_base/* /bin/
COPY marketplace/deployer_util/* /bin/
ARG VERSION
RUN echo "$VERSION" > /version

RUN mkdir -p /data/manifest

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
