FROM python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-openssl \
        python3-pip \
        python3-setuptools \
        python3-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install wheel \
    && pip3 install google-cloud-storage

# Install lint tools.
RUN pip3 install futures pyflakes yapf
