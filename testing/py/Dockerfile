FROM python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python-pip \
	python-setuptools \
        python-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN pip2 install wheel \
    && pip2 install google-cloud-storage

# Install lint tools.
RUN pip2 install futures pyflakes yapf
