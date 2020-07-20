FROM gcr.io/google-appengine/python

RUN pip3 install \
      futures \
      google-cloud-storage \
      pyflakes \
      pyOpenSSL \
      pyyaml \
      wheel \
      yapf \
      coverage

COPY runtests.sh /bin/
