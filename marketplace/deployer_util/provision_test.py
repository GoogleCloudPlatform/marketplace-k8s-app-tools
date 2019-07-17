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

import unittest

import provision
from provision import dns1123_name
from provision import limit_name

import config_helper


def mock_get_canonical_image_pull_secret_manifest(
    canonical_image_pull_secret_name, target_namespace):
  return {
      'apiVersion': 'v1',
      'kind': 'Secret',
      'metadata': {
          'name': canonical_image_pull_secret_name,
          'namespace': target_namespace,
      },
      'data': {
          'some-key': 'some-data',
      },
  }


class ProvisionTest(unittest.TestCase):

  def test_dns1123_name(self):
    self.assertEqual(dns1123_name('valid-name'), 'valid-name')
    self.assertEqual(dns1123_name('aA'), 'aa')
    self.assertEqual(
        dns1123_name('*sp3cial-@chars.(rem0ved^'), 'sp3cial-chars-rem0ved')
    self.assertEqual(dns1123_name('-abc.def.'), 'abc-def')
    self.assertEqual(dns1123_name('-123.456.'), '123-456')
    self.assertModifiedName(
        dns1123_name('Lorem-Ipsum-is-simply-dummy-text-of-the-printing-and-'
                     'typesettings-----------------------------------------'),
        'lorem-ipsum-is-simply-dummy-text-of-the-printing-and-typese')
    self.assertModifiedName(
        dns1123_name('Lorem-Ipsum-is-simply-dummy-text-of-the-printing-and-'
                     'typesettings.........................................'),
        'lorem-ipsum-is-simply-dummy-text-of-the-printing-and-typese')

  def test_limit_name(self):
    self.assertEqual(limit_name('valid-name'), 'valid-name')
    self.assertEqual(limit_name('valid-name', 8), 'val-030a')

  def assertModifiedName(self, text, expected):
    self.assertEqual(text[:-5], expected)
    self.assertRegexpMatches(text[-5:], r'-[a-f0-9]{4}')

  def test_deployer_image_inject(self):
    schema = config_helper.Schema.load_yaml('''
    properties:
      deployer_image:
        type: string
        x-google-marketplace:
          type: DEPLOYER_IMAGE
    ''')
    values = {}
    deployer_image = 'gcr.io/cloud-marketplace/partner/solution/deployer:latest'
    self.assertEquals(
        provision.inject_deployer_image_properties(values, schema,
                                                   deployer_image),
        {"deployer_image": deployer_image})

  def test_deployer_image_to_repo_prefix(self):
    self.assertEqual(
        'gcr.io/test',
        provision.deployer_image_to_repo_prefix('gcr.io/test/deployer'))
    self.assertEqual(
        'gcr.io/test',
        provision.deployer_image_to_repo_prefix('gcr.io/test/deployer:0.1.1'))
    self.assertEqual(
        'gcr.io/test',
        provision.deployer_image_to_repo_prefix(
            'gcr.io/test/deployer@sha256:0123456789abcdef'))
    with self.assertRaises(Exception):
      provision.deployer_image_to_repo_prefix('gcr.io/test/test')
    with self.assertRaises(Exception):
      provision.deployer_image_to_repo_prefix(
          'gcr.io/test/test@sha256:0123456789abcdef')
    with self.assertRaises(Exception):
      provision.deployer_image_to_repo_prefix('gcr.io/test/test:0.1.1')

  def test_provision_service_account_image_pull_secrets(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          sa:
            type: string
            x-google-marketplace:
              type: SERVICE_ACCOUNT
              serviceAccount:
                roles:
                - type: ClusterRole
                  rulesType: PREDEFINED
                  rulesFromRoleName: cluster-admin
        """)
    manifests = provision.provision_service_account(
        schema, schema.properties['sa'], 'app-name-1', 'namespace-1',
        'image-pull-secret-1', 'canonical-image-pull-secret-1',
        mock_get_canonical_image_pull_secret_manifest)
    self.assertIn(
        {
            'apiVersion':
                'v1',
            'kind':
                'ServiceAccount',
            'metadata': {
                'name': 'app-name-1-sa',
                'namespace': 'namespace-1',
            },
            'imagePullSecrets': [{
                'name': 'image-pull-secret-1'
            }, {
                'name': 'canonical-image-pull-secret-1',
            }],
        }, manifests)
    self.assertIn(
        mock_get_canonical_image_pull_secret_manifest(
            'canonical-image-pull-secret-1', 'namespace-1'), manifests)

  def test_provision_deployer_image_pull_secrets(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          # v2 required fields
          schemaVersion: v2
          applicationApiVersion: v1beta1
          publishedVersion: 6.5.130
          publishedVersionMetadata:
            releaseNote: Bug fixes
            releaseTypes:
            - BUG_FIX
          images:
            main:
              properties:
                main.image:
                  type: FULL
          deployerServiceAccount:
            roles:
            - type: ClusterRole
              rulesType: PREDEFINED
              rulesFromRoleName: cluster-admin
        properties:
          simple:
            type: string
        """)
    manifests = provision.provision_deployer(
        schema,
        'app-name-1',
        'namespace-1',
        'gcr.io/some-repo/some-app/deployer:1.0',
        None,  # deployer_entrypoint
        dict({'simple': 'some-value'}),
        'image-pull-secret-1',
        'canonical-image-pull-secret-1',
        mock_get_canonical_image_pull_secret_manifest)
    self.assertIn(
        {
            'apiVersion':
                'v1',
            'kind':
                'ServiceAccount',
            'metadata': {
                'name': 'app-name-1-deployer-sa',
                'namespace': 'namespace-1',
                'labels': {
                    'app.kubernetes.io/component':
                        'deployer.marketplace.cloud.google.com',
                    'marketplace.cloud.google.com/deployer':
                        'Dependent',
                },
            },
            'imagePullSecrets': [{
                'name': 'image-pull-secret-1'
            }, {
                'name': 'canonical-image-pull-secret-1',
            }],
        }, manifests)
    self.assertIn(
        mock_get_canonical_image_pull_secret_manifest(
            'canonical-image-pull-secret-1', 'namespace-1'), manifests)

  def test_provision_kalm_image_pull_secrets(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130
          publishedVersionMetadata:
            releaseNote: Bug fixes
            releaseTypes:
            - BUG_FIX
            recommended: true

          managedUpdates:
            kalmSupported: true

          images:
            main:
              properties:
                main.image:
                  type: FULL
            db:
              properties:
                db.image.repo:
                  type: REPO_WITH_REGISTRY
                db.image.tag:
                  type: TAG
        properties:
          simple:
            type: string
        """)
    manifests = provision.provision_kalm(
        schema, 'version-repo-1', 'app-name-1',
        'namespace-1', 'gcr.io/some-repo/some-app/deployer:1.0',
        dict({'simple': 'some-value'}), 'image-pull-secret-1',
        'canonical-image-pull-secret-1',
        mock_get_canonical_image_pull_secret_manifest)
    self.assertIn(
        {
            'apiVersion':
                'v1',
            'kind':
                'ServiceAccount',
            'metadata': {
                'name': 'app-name-1-deployer-sa',
                'namespace': 'namespace-1',
                'labels': {
                    'app.kubernetes.io/component':
                        'kalm.marketplace.cloud.google.com',
                },
            },
            'imagePullSecrets': [{
                'name': 'image-pull-secret-1'
            }, {
                'name': 'canonical-image-pull-secret-1',
            }],
        }, manifests)
    self.assertIn(
        mock_get_canonical_image_pull_secret_manifest(
            'canonical-image-pull-secret-1', 'namespace-1'), manifests)
