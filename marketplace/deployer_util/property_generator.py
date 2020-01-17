# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import OpenSSL
import random

from password import GeneratePassword


def generate_password(config):
  """Generate password value for SchemaXPassword config."""
  pw = GeneratePassword(config.length, config.include_symbols)
  if config.base64:
    pw = base64.b64encode(pw.encode('utf-8')).decode()
  return pw


def generate_tls_certificate():
  """Generate TLS value, a json string."""
  cert_seconds_to_expiry = 60 * 60 * 24 * 365  # one year

  key = OpenSSL.crypto.PKey()
  key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

  cert = OpenSSL.crypto.X509()
  cert.get_subject().OU = 'GCP Marketplace K8s App Tools'
  cert.get_subject().CN = 'Temporary Certificate'
  cert.gmtime_adj_notBefore(0)
  cert.gmtime_adj_notAfter(cert_seconds_to_expiry)
  cert.set_serial_number(random.getrandbits(64))
  cert.set_issuer(cert.get_subject())
  cert.set_pubkey(key)
  cert.sign(key, 'sha256')

  return json.dumps({
      'private_key':
          OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                         key).decode('ascii'),
      'certificate':
          OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM,
                                          cert).decode('ascii')
  })
