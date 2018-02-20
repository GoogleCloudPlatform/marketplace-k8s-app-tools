FROM launcher.gcr.io/google/debian9

COPY build/kubectl bin
COPY marketplace/deployer_kubectl_base/deploy.sh bin

RUN apt-get update
RUN apt-get install -y apt-utils bash gettext jq

RUN mkdir data
RUN mkdir data/manifest

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
