FROM launcher.gcr.io/google/debian9

COPY build/kubectl bin
COPY build/helm bin
COPY marketplace/deployer_helm_base/deploy.sh bin

RUN apt-get update
RUN apt-get install -y apt-utils bash gettext jq

RUN mkdir data
RUN mkdir data/chart

ENTRYPOINT ["/bin/bash", "/bin/deploy.sh"]
