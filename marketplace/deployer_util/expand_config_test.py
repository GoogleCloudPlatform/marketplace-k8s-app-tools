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
import re
import OpenSSL
import tempfile
import unittest

import config_helper
import expand_config


class ExpandConfigTest(unittest.TestCase):

  def test_defaults(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          p1:
            type: string
            default: Default
        """)
    self.assertEqual({'p1': 'Default'}, expand_config.expand({}, schema))
    self.assertEqual({'p1': 'Mine'}, expand_config.expand({'p1': 'Mine'},
                                                          schema))

  def test_invalid_value_type(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          p1:
            type: string
        """)
    self.assertRaises(expand_config.InvalidProperty,
                      lambda: expand_config.expand({'p1': 3}, schema))

  def test_generate_properties_for_v1_image_split_by_colon(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          i1:
            type: string
            default: gcr.io/google/busybox:1.0
            x-google-marketplace:
              type: IMAGE
              image:
                generatedProperties:
                  splitByColon:
                    before: i1.before
                    after: i1.after
        """)
    result = expand_config.expand({'i1': 'gcr.io/foo:bar'}, schema)
    self.assertEqual(
        {
            'i1': 'gcr.io/foo:bar',
            'i1.before': 'gcr.io/foo',
            'i1.after': 'bar',
        }, result)

  def test_generate_properties_for_v1_image_split_to_registry_repo_tag(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          i1:
            type: string
            default: gcr.io/google/busybox:1.0
            x-google-marketplace:
              type: IMAGE
              image:
                generatedProperties:
                  splitToRegistryRepoTag:
                    registry: i1.registry
                    repo: i1.repo
                    tag: i1.tag
        """)
    result = expand_config.expand({'i1': 'gcr.io/foo/bar:baz'}, schema)
    self.assertEqual(
        {
            'i1': 'gcr.io/foo/bar:baz',
            'i1.registry': 'gcr.io',
            'i1.repo': 'foo/bar',
            'i1.tag': 'baz',
        }, result)

  def test_generate_properties_for_v2_images(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2
          applicationApiVersion: v1beta1
          publishedVersion: '0.1.1'
          publishedVersionMetadata:
            releaseNote: Release note for 0.1.1
          images:
            "":
              properties:
                image.full: {type: FULL}
                image.registry: {type: REGISTRY}
                image.registry_repo: {type: REPO_WITH_REGISTRY}
                image.repo: {type: REPO_WITHOUT_REGISTRY}
                image.tag: {type: TAG}
            i1:
              properties:
                image.i1.full: {type: FULL}
                image.i1.registry: {type: REGISTRY}
                image.i1.registry_repo: {type: REPO_WITH_REGISTRY}
                image.i1.repo: {type: REPO_WITHOUT_REGISTRY}
                image.i1.tag: {type: TAG}
            i2:
              properties:
                image.i2.full: {type: FULL}
                image.i2.registry: {type: REGISTRY}
                image.i2.registry_repo: {type: REPO_WITH_REGISTRY}
                image.i2.repo: {type: REPO_WITHOUT_REGISTRY}
                image.i2.tag: {type: TAG}
        """)
    result = expand_config.expand({'__image_repo_prefix__': 'gcr.io/app'},
                                  schema)
    self.assertEqual(
        {
            'image.full': 'gcr.io/app:0.1.1',
            'image.tag': '0.1.1',
            'image.registry': 'gcr.io',
            'image.registry_repo': 'gcr.io/app',
            'image.repo': 'app',
            'image.i1.full': 'gcr.io/app/i1:0.1.1',
            'image.i1.tag': '0.1.1',
            'image.i1.registry': 'gcr.io',
            'image.i1.registry_repo': 'gcr.io/app/i1',
            'image.i1.repo': 'app/i1',
            'image.i2.full': 'gcr.io/app/i2:0.1.1',
            'image.i2.tag': '0.1.1',
            'image.i2.registry': 'gcr.io',
            'image.i2.registry_repo': 'gcr.io/app/i2',
            'image.i2.repo': 'app/i2',
        }, result)

  def test_deployer_image_in_v2(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2
          applicationApiVersion: v1beta1
          publishedVersion: '0.1.1'
          publishedVersionMetadata:
            releaseNote: Release note for 0.1.1
          images:
            "":
              properties:
                image.full: {type: FULL}
        properties:
          deployerImage:
            type: string
            x-google-marketplace:
              type: DEPLOYER_IMAGE
        """)
    result = expand_config.expand({'__image_repo_prefix__': 'gcr.io/app'},
                                  schema)
    self.assertEqual(
        {
            'image.full': 'gcr.io/app:0.1.1',
            'deployerImage': 'gcr.io/app/deployer:0.1.1',
        }, result)

  def test_generate_properties_for_string_base64_encoded(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          s1:
            type: string
            x-google-marketplace:
              type: STRING
              string:
                generatedProperties:
                  base64Encoded: s1.encoded
        """)
    result = expand_config.expand({'s1': 'test'}, schema)
    self.assertEqual({
        's1': 'test',
        's1.encoded': b'dGVzdA==',
    }, result)

  def test_generate_certificate(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          c1:
            type: string
            x-google-marketplace:
              type: TLS_CERTIFICATE
        """)
    result = expand_config.expand({}, schema)
    cert_json = json.loads(result['c1'])
    self.assertIsNotNone(cert_json['private_key'])
    self.assertIsNotNone(cert_json['certificate'])

    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          c1:
            type: string
            x-google-marketplace:
              type: TLS_CERTIFICATE
              tlsCertificate:
                generatedProperties:
                  base64EncodedPrivateKey: c1.Base64Key
                  base64EncodedCertificate: c1.Base64Crt
        """)
    result = expand_config.expand({}, schema)

    self.assertIsNotNone(result['c1'])
    cert_json = json.loads(result['c1'])
    self.assertEqual(
        result['c1.Base64Key'],
        base64.b64encode(
            cert_json['private_key'].encode('ascii')).decode('ascii'))
    self.assertEqual(
        result['c1.Base64Crt'],
        base64.b64encode(
            cert_json['certificate'].encode('ascii')).decode('ascii'))

    key = OpenSSL.crypto.load_privatekey(
        OpenSSL.crypto.FILETYPE_PEM, base64.b64decode(result['c1.Base64Key']))
    self.assertEqual(key.bits(), 2048)
    self.assertEqual(key.type(), OpenSSL.crypto.TYPE_RSA)

    cert = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM, base64.b64decode(result['c1.Base64Crt']))
    self.assertEqual(cert.get_subject(), cert.get_issuer())
    self.assertEqual(cert.get_subject().OU, 'GCP Marketplace K8s App Tools')
    self.assertEqual(cert.get_subject().CN, 'Temporary Certificate')
    self.assertEqual(cert.get_signature_algorithm(), b'sha256WithRSAEncryption')
    self.assertFalse(cert.has_expired())

  def test_generate_properties_for_certificate(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          c1:
            type: string
            x-google-marketplace:
              type: TLS_CERTIFICATE
        """)
    result = expand_config.expand(
        {'c1': '{"private_key": "key", "certificate": "vrt"}'}, schema)
    self.assertEqual({'c1': '{"private_key": "key", "certificate": "vrt"}'},
                     result)

    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          c1:
            type: string
            x-google-marketplace:
              type: TLS_CERTIFICATE
              tlsCertificate:
                generatedProperties:
                  base64EncodedPrivateKey: c1.Base64Key
                  base64EncodedCertificate: c1.Base64Crt
        """)
    result = expand_config.expand(
        {'c1': '{"private_key": "key", "certificate": "vrt"}'}, schema)

    self.assertEqual(
        {
            'c1': '{"private_key": "key", "certificate": "vrt"}',
            'c1.Base64Key': 'a2V5',
            'c1.Base64Crt': 'dnJ0',
        }, result)

  def test_generate_password(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          p1:
            type: string
            x-google-marketplace:
              type: GENERATED_PASSWORD
              generatedPassword:
                length: 8
                includeSymbols: false
                base64: false
        """)
    result = expand_config.expand({}, schema)
    self.assertEqual({'p1'}, set(result))
    self.assertIsNotNone(re.match(r'^[a-zA-Z0-9]{8}$', result['p1']))

  def test_application_uid(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          application_uid:
            type: string
            x-google-marketplace:
              type: APPLICATION_UID
              applicationUid:
                generatedProperties:
                  createApplicationBoolean: application.create
        """)
    result = expand_config.expand({}, schema, app_uid='1234-abcd')
    self.assertEqual(
        {
            'application_uid': '1234-abcd',
            'application.create': False
        }, result)
    result = expand_config.expand({}, schema, app_uid='')
    self.assertEqual({
        'application_uid': '',
        'application.create': True
    }, result)

  def test_istio_enabled_backward_compatibility(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          istioEnabled:
            type: boolean
            x-google-marketplace:
              type: ISTIO_ENABLED
        """)
    result = expand_config.expand({}, schema)
    self.assertEqual({'istioEnabled': False}, result)
    result = expand_config.expand({'istioEnabled': True}, schema)
    self.assertEqual({'istioEnabled': True}, result)

  def test_ingress_available_backward_compatibility(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          ingressAvail:
            type: boolean
            x-google-marketplace:
              type: INGRESS_AVAILABLE
        """)
    result = expand_config.expand({}, schema)
    self.assertEqual({'ingressAvail': True}, result)
    result = expand_config.expand({'ingressAvail': False}, schema)
    self.assertEqual({'ingressAvail': False}, result)

  def test_write_values(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          propertyInt:
            type: int
          propertyStr:
            type: string
          propertyNum:
            type: number
        """)
    values = {'propertyInt': 4, 'propertyStr': 'Value', 'propertyNum': 1.0}
    with tempfile.NamedTemporaryFile('w') as tf:
      expand_config.write_values(values, tf.name)
      actual = config_helper.load_values(tf.name, '/non/existent/dir', schema)
      self.assertEqual(values, actual)
