FROM gcr.io/cloud-marketplace/google/ubuntu2204

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip

RUN pip3 install \
      google-cloud-storage \
      pyflakes \
      pyOpenSSL \
      pyyaml \
      wheel \
      yapf \
      coverage

COPY runtests.sh /bin/
