FROM alpine

COPY build/kubectl bin
COPY marketplace/controller/controller.sh bin

RUN apk update && apk add bash gettext jq

ENTRYPOINT ["/bin/bash", "/bin/controller.sh"]
