FROM python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python-openssl \
        python-pip \
        python-setuptools \
        python-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install wheel \
    && pip3 install google-cloud-storage

# Install lint tools.
RUN pip3 install futures pyflakes yapf
