FROM python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libssl-dev \
        python-pip \
        python-setuptools \
        python-yaml \
    && rm -rf /var/lib/apt/lists/* \
    && pip2 install \
        futures \
        google-cloud-storage \
        pyflakes \
        pyopenssl \
        yapf
