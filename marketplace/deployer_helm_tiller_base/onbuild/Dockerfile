ARG FROM
FROM $FROM

ONBUILD COPY . /tmp/onbuild

ONBUILD ARG HELM_DEPENDENCY_BUILD=false
ONBUILD ENV HELM_DEPENDENCY_BUILD $HELM_DEPENDENCY_BUILD

# Partner directory structure assertions.
ONBUILD RUN if [ "$(find /tmp/onbuild/chart -maxdepth 1 -mindepth 1 -type d -printf '\n' | wc -l)" -ne 1 ]; then \
              >&2 echo "Too many charts in chart/." ; \
              find /tmp/onbuild ; \
              exit 1 ; \
            fi ; \
            if [ ! -f /tmp/onbuild/schema.yaml ]; then \
              >&2 echo "Missing schema.yaml." ; \
              find /tmp/onbuild ; \
              exit 1 ; \
            fi

ONBUILD RUN export CHART_NAME="$(find /tmp/onbuild/chart -maxdepth 1 -mindepth 1 -type d -printf '%P\n')" \
            && cp /tmp/onbuild/schema.yaml /data/schema.yaml \
            && mkdir -p /data/chart \
            && cd /data/chart \
            && if [ "$HELM_DEPENDENCY_BUILD" = "true" ]; then \
                 helm dependency build "/tmp/onbuild/chart/$CHART_NAME" ; \
               fi \
            && helm package "/tmp/onbuild/chart/$CHART_NAME" --destination /data/chart/ \
            && rm -rf /tmp/onbuild
