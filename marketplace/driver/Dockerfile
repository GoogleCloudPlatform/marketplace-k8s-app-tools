FROM launcher.gcr.io/google/debian9

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*
RUN wget -q -O /bin/kubectl \
        https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl \
    && chmod 755 /bin/kubectl
RUN apt-get install uuid-runtime\
RUN apt-get update \
    && apt-get install -y --no-install-recommends apt-utils bash gettext jq

COPY marketplace/driver/* /bin/
COPY scripts/start.sh /bin/scripts
COPY scripts/stop.sh /bin/scripts

ENV MARKETPLACE_TOOLS /bin/
ENV KUBECONFIG /bin/.kube/config
ENV APP_NAME application

# ENTRYPOINT ["/bin/bash", "/bin/driver.sh --app_name=APP_NAME --deployer=$DEPLOYER_IMAGE --marketplace_tools=$MARKETPLACE_TOOLS]
