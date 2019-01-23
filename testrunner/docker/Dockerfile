# Copyright 2018 Google LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM launcher.gcr.io/google/debian9

COPY testrunner /bin/testrunner

RUN apt-get update && \
	    apt-get install -y --no-install-recommends wget && \
	    rm -rf /var/lib/apt/lists/*

COPY oss.sha512.checksums /oss.sha512.checksums

RUN set -xeu && \
      mkdir -p /usr/share/testrunner && \
      wget -q -O /usr/share/testrunner/testrunner.LICENSE https://raw.githubusercontent.com/GoogleCloudPlatform/marketplace-k8s-app-tools/master/LICENSE && \
      wget -q -O /usr/share/testrunner/go-yaml.LICENSE https://raw.githubusercontent.com/go-yaml/yaml/v2.2.1/LICENSE && \
      wget -q -O /usr/share/testrunner/go-yaml.LICENSE.libyaml https://raw.githubusercontent.com/go-yaml/yaml/v2.2.1/LICENSE.libyaml && \
      wget -q -O /usr/share/testrunner/go-xmlpath.LICENSE https://raw.githubusercontent.com/go-xmlpath/xmlpath/v2/LICENSE && \
      wget -q -O /usr/share/testrunner/glog.LICENSE https://raw.githubusercontent.com/golang/glog/master/LICENSE && \
      wget -q -O /usr/share/testrunner/ghodss-yaml.LICENSE https://raw.githubusercontent.com/ghodss/yaml/master/LICENSE && \
      mkdir -p /usr/local/src/xmlpath && \
      wget -q -O /usr/local/src/xmlpath/xmlpath.v2.zip https://github.com/go-xmlpath/xmlpath/archive/v2.zip && \
      sha512sum -c oss.sha512.checksums --status

ENTRYPOINT ["/bin/testrunner"]
