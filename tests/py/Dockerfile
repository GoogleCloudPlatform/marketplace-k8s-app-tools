FROM gcr.io/google-appengine/python

RUN pip install \
      futures \
      google-cloud-storage \
      pyflakes \
      pyOpenSSL \
      pyyaml \
      wheel \
      yapf \
      coverage

COPY runtests.sh /bin/
