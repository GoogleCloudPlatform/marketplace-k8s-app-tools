FROM python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python-pip \
	python-setuptools \
        python-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN /usr/bin/env python2 -m pip install google-cloud-storage
