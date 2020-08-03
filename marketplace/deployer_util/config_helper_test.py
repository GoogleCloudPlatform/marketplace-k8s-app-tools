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

import os
import tempfile
import unittest

import config_helper

SCHEMA = """
properties:
  propertyString:
    type: string
  propertyStringWithDefault:
    type: string
    default: DefaultString
  propertyInt:
    type: int
  propertyIntWithDefault:
    type: int
    default: 3
  propertyInteger:
    type: integer
  propertyIntegerWithDefault:
    type: integer
    default: 6
  propertyNumber:
    type: number
  propertyNumberWithDefault:
    type: number
    default: 1.0
  propertyBoolean:
    type: boolean
  propertyBooleanWithDefault:
    type: boolean
    default: false
  propertyImage:
    type: string
    default: gcr.io/google/busybox:1.0
    x-google-marketplace:
      type: IMAGE
  propertyDeployerImage:
    type: string
    x-google-marketplace:
      type: DEPLOYER_IMAGE
  propertyPassword:
    type: string
    x-google-marketplace:
      type: GENERATED_PASSWORD
      length: 4
  applicationUid:
    type: string
    x-google-marketplace:
      type: APPLICATION_UID
  istioEnabled:
    type: boolean
    x-google-marketplace:
      type: ISTIO_ENABLED
  ingressAvailable:
    type: boolean
    x-google-marketplace:
      type: INGRESS_AVAILABLE
  certificate:
    type: string
    x-google-marketplace:
      type: TLS_CERTIFICATE
      tlsCertificate:
        generatedProperties:
          base64EncodedPrivateKey: keyEncoded
          base64EncodedCertificate: crtEncoded
  customSecret:
    title: Secret needed by the app.
    description: User-entered text to be masked in the UI.
    type: string
    x-google-marketplace:
      type: MASKED_FIELD
required:
- propertyString
- propertyPassword
form:
- widget: help
  description: My arbitrary <i>description</i>
"""


class ConfigHelperTest(unittest.TestCase):

  def test_load_yaml_file(self):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8') as f:
      f.write(SCHEMA)
      f.flush()

      schema = config_helper.Schema.load_yaml_file(f.name)
      schema_from_str = config_helper.Schema.load_yaml(SCHEMA)
      self.assertEqual(schema.properties, schema_from_str.properties)
      self.assertEqual(schema.required, schema_from_str.required)
      self.assertEqual(schema.form, schema_from_str.form)

  def test_bad_required(self):

    def load_and_validate(schema_yaml):
      schema = config_helper.Schema.load_yaml(schema_yaml)
      schema.validate()

    schema_yaml = """
                  properties:
                    propertyA:
                      type: string
                  required:
                  - propertyA
                  - propertyB
                  - propertyC
                  """
    self.assertRaisesRegex(config_helper.InvalidSchema, r'propertyB, propertyC',
                           load_and_validate, schema_yaml)

  def test_types_and_defaults(self):
    schema = config_helper.Schema.load_yaml(SCHEMA)
    self.assertEqual(
        {
            'propertyString', 'propertyStringWithDefault', 'propertyInt',
            'propertyIntWithDefault', 'propertyInteger',
            'propertyIntegerWithDefault', 'propertyNumber',
            'propertyNumberWithDefault', 'propertyBoolean',
            'propertyBooleanWithDefault', 'propertyImage',
            'propertyDeployerImage', 'propertyPassword', 'applicationUid',
            'istioEnabled', 'ingressAvailable', 'certificate', 'customSecret'
        }, set(schema.properties))
    self.assertEqual(str, schema.properties['propertyString'].type)
    self.assertIsNone(schema.properties['propertyString'].default)
    self.assertEqual(str, schema.properties['propertyStringWithDefault'].type)
    self.assertEqual('DefaultString',
                     schema.properties['propertyStringWithDefault'].default)
    self.assertEqual(int, schema.properties['propertyInt'].type)
    self.assertIsNone(schema.properties['propertyInt'].default)
    self.assertEqual(int, schema.properties['propertyIntWithDefault'].type)
    self.assertEqual(3, schema.properties['propertyIntWithDefault'].default)
    self.assertEqual(int, schema.properties['propertyInteger'].type)
    self.assertIsNone(schema.properties['propertyInteger'].default)
    self.assertEqual(int, schema.properties['propertyIntegerWithDefault'].type)
    self.assertEqual(6, schema.properties['propertyIntegerWithDefault'].default)
    self.assertEqual(float, schema.properties['propertyNumber'].type)
    self.assertIsNone(schema.properties['propertyNumber'].default)
    self.assertEqual(float, schema.properties['propertyNumberWithDefault'].type)
    self.assertEqual(1.0,
                     schema.properties['propertyNumberWithDefault'].default)
    self.assertEqual(bool, schema.properties['propertyBoolean'].type)
    self.assertIsNone(schema.properties['propertyBoolean'].default)
    self.assertEqual(bool, schema.properties['propertyBooleanWithDefault'].type)
    self.assertEqual(False,
                     schema.properties['propertyBooleanWithDefault'].default)
    self.assertEqual(str, schema.properties['propertyImage'].type)
    self.assertEqual('gcr.io/google/busybox:1.0',
                     schema.properties['propertyImage'].default)
    self.assertEqual('IMAGE', schema.properties['propertyImage'].xtype)
    self.assertEqual('DEPLOYER_IMAGE',
                     schema.properties['propertyDeployerImage'].xtype)
    self.assertEqual(str, schema.properties['propertyPassword'].type)
    self.assertIsNone(schema.properties['propertyPassword'].default)
    self.assertEqual('GENERATED_PASSWORD',
                     schema.properties['propertyPassword'].xtype)
    self.assertEqual('My arbitrary <i>description</i>',
                     schema.form[0]['description'])
    self.assertEqual(bool, schema.properties['istioEnabled'].type)
    self.assertEqual('ISTIO_ENABLED', schema.properties['istioEnabled'].xtype)
    self.assertEqual(bool, schema.properties['ingressAvailable'].type)
    self.assertEqual('INGRESS_AVAILABLE',
                     schema.properties['ingressAvailable'].xtype)
    self.assertEqual(str, schema.properties['certificate'].type)
    self.assertEqual('TLS_CERTIFICATE', schema.properties['certificate'].xtype)
    self.assertEqual('MASKED_FIELD', schema.properties['customSecret'].xtype)

  def test_invalid_names(self):
    self.assertRaises(
        config_helper.InvalidSchema, lambda: config_helper.Schema.load_yaml("""
            properties:
              bad/name:
                type: string
            """))

  def test_valid_names(self):
    config_helper.Schema.load_yaml("""
        properties:
          a-good_name:
            type: string
        """)

  def test_invalid_property_types(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*must be of type string$',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: integer
                x-google-marketplace:
                  type: NAME
            """))
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*must be of type string$',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: number
                x-google-marketplace:
                  type: NAMESPACE
            """))
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*must be of type string$',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: int
                x-google-marketplace:
                  type: DEPLOYER_IMAGE
            """))
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*must be of type string$',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: boolean
                x-google-marketplace:
                  type: APPLICATION_UID
            """))
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*must be of type boolean$',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: string
                x-google-marketplace:
                  type: ISTIO_ENABLED
            """))
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*must be of type boolean$',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: string
                x-google-marketplace:
                  type: INGRESS_AVAILABLE
            """))

  def test_required(self):
    schema = config_helper.Schema.load_yaml(SCHEMA)
    self.assertTrue(schema.properties['propertyString'].required)
    self.assertTrue(schema.properties['propertyPassword'].required)
    self.assertFalse(schema.properties['propertyInt'].required)
    self.assertFalse(schema.properties['propertyNumberWithDefault'].required)

  def test_schema_properties_matching(self):
    schema = config_helper.Schema.load_yaml(SCHEMA)
    self.assertEqual([schema.properties['propertyPassword']],
                     schema.properties_matching({
                         'x-google-marketplace': {
                             'type': 'GENERATED_PASSWORD'
                         }
                     }))
    self.assertEqual([
        schema.properties['propertyInt'],
        schema.properties['propertyIntWithDefault']
    ], schema.properties_matching({
        'type': 'int',
    }))

  def test_name_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          n:
            type: string
            x-google-marketplace:
              type: NAME
        """)
    self.assertIsNotNone(schema.properties['n'])

  def test_namespace_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          ns:
            type: string
            x-google-marketplace:
              type: NAMESPACE
        """)
    self.assertIsNotNone(schema.properties['ns'])

  def test_application_uid_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          u:
            type: string
            x-google-marketplace:
              type: APPLICATION_UID
        """)
    self.assertIsNotNone(schema.properties['u'].application_uid)
    self.assertIsNone(schema.properties['u'].application_uid.application_create)

  def test_application_uid_type_create_application(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          u:
            type: string
            x-google-marketplace:
              type: APPLICATION_UID
              applicationUid:
                generatedProperties:
                  createApplicationBoolean: application.create
        """)
    self.assertIsNotNone(schema.properties['u'].application_uid)
    self.assertEqual('application.create',
                     schema.properties['u'].application_uid.application_create)

  def test_image_default_missing(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, r'.*default image value must be specified',
        lambda: config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            x-google-marketplace:
              type: IMAGE
        """))

  def test_image_default_missing_repo(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema,
        r'.*default image value must state registry',
        lambda: config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            default: $REGISTRY/some-repo:some-tag
            x-google-marketplace:
              type: IMAGE
        """))

  def test_image_default_missing_tag_or_digest(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema,
        r'.*default image value is missing a tag or digest',
        lambda: config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            default: gcr.io/some-repo
            x-google-marketplace:
              type: IMAGE
        """))

  def test_image_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            default: gcr.io/some-repo:some-tag
            x-google-marketplace:
              type: IMAGE
        """)
    self.assertIsNotNone(schema.properties['i'].image)
    self.assertIsNone(schema.properties['i'].image.split_by_colon)
    self.assertIsNone(schema.properties['i'].image.split_to_registry_repo_tag)

  def test_image_type_splitbycolon(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            default: gcr.io/some-repo:some-tag
            x-google-marketplace:
              type: IMAGE
              image:
                generatedProperties:
                  splitByColon:
                    before: image.before
                    after: image.after
        """)
    self.assertIsNotNone(schema.properties['i'].image)
    self.assertEqual(('image.before', 'image.after'),
                     schema.properties['i'].image.split_by_colon)

  def test_image_type_splittoregistryrepotag(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            default: gcr.io/some-repo:some-tag
            x-google-marketplace:
              type: IMAGE
              image:
                generatedProperties:
                  splitToRegistryRepoTag:
                    registry: image.registry
                    repo: image.repo
                    tag: image.tag
        """)
    self.assertIsNotNone(schema.properties['i'].image)
    self.assertEqual(('image.registry', 'image.repo', 'image.tag'),
                     schema.properties['i'].image._split_to_registry_repo_tag)

  def test_deployer_image_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          di:
            type: string
            default: gcr.io/some-repo:some-tag
            x-google-marketplace:
              type: DEPLOYER_IMAGE
        """)
    self.assertIsNotNone(schema.properties['di'])

  def test_password(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          pw:
            type: string
            x-google-marketplace:
              type: GENERATED_PASSWORD
        """)
    self.assertEqual(10, schema.properties['pw'].password.length)
    self.assertEqual(False, schema.properties['pw'].password.include_symbols)
    self.assertEqual(True, schema.properties['pw'].password.base64)

    schema = config_helper.Schema.load_yaml("""
        properties:
          pw:
            type: string
            x-google-marketplace:
              type: GENERATED_PASSWORD
              generatedPassword:
                length: 5
                includeSymbols: true
                base64: false
        """)
    self.assertEqual(5, schema.properties['pw'].password.length)
    self.assertEqual(True, schema.properties['pw'].password.include_symbols)
    self.assertEqual(False, schema.properties['pw'].password.base64)

  def test_certificate(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          c1:
            type: string
            x-google-marketplace:
              type: TLS_CERTIFICATE
        """)

    self.assertIsNotNone(schema.properties['c1'].tls_certificate)
    self.assertIsNone(
        schema.properties['c1'].tls_certificate.base64_encoded_private_key)
    self.assertIsNone(
        schema.properties['c1'].tls_certificate.base64_encoded_certificate)

    schema = config_helper.Schema.load_yaml("""
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
    self.assertIsNotNone(schema.properties['c1'].tls_certificate)
    self.assertEqual(
        'c1.Base64Key',
        schema.properties['c1'].tls_certificate.base64_encoded_private_key)
    self.assertEqual(
        'c1.Base64Crt',
        schema.properties['c1'].tls_certificate.base64_encoded_certificate)

  def test_int_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          pi:
            type: int
        """)
    self.assertEqual(5, schema.properties['pi'].str_to_type('5'))

  def test_number_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          pn:
            type: number
        """)
    self.assertEqual(5.2, schema.properties['pn'].str_to_type('5.2'))

  def test_boolean_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          pb:
            type: boolean
        """)
    self.assertEqual(True, schema.properties['pb'].str_to_type('true'))
    self.assertEqual(True, schema.properties['pb'].str_to_type('True'))
    self.assertEqual(True, schema.properties['pb'].str_to_type('yes'))
    self.assertEqual(True, schema.properties['pb'].str_to_type('Yes'))
    self.assertEqual(False, schema.properties['pb'].str_to_type('false'))
    self.assertEqual(False, schema.properties['pb'].str_to_type('False'))
    self.assertEqual(False, schema.properties['pb'].str_to_type('no'))
    self.assertEqual(False, schema.properties['pb'].str_to_type('No'))
    self.assertRaises(config_helper.InvalidValue,
                      lambda: schema.properties['pb'].str_to_type('bad'))

  def test_invalid_default_type(self):
    self.assertRaises(
        config_helper.InvalidSchema, lambda: config_helper.Schema.load_yaml("""
            properties:
              pn:
                type: number
                default: abc
            """))

  def test_property_matches_definition(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          propertyInt:
            type: int
          propertyPassword:
            type: string
            x-google-marketplace:
              type: GENERATED_PASSWORD
        """)
    self.assertTrue(schema.properties['propertyInt'].matches_definition(
        {'name': 'propertyInt'}))
    self.assertFalse(schema.properties['propertyInt'].matches_definition(
        {'name': 'propertyPassword'}))
    self.assertTrue(schema.properties['propertyInt'].matches_definition(
        {'type': 'int'}))
    self.assertFalse(schema.properties['propertyInt'].matches_definition(
        {'type': 'string'}))
    self.assertFalse(schema.properties['propertyInt'].matches_definition(
        {'x-google-marketplace': {
            'type': 'GENERATED_PASSWORD'
        }}))
    self.assertTrue(schema.properties['propertyPassword'].matches_definition(
        {'x-google-marketplace': {
            'type': 'GENERATED_PASSWORD'
        }}))
    self.assertTrue(schema.properties['propertyPassword'].matches_definition({
        'type': 'string',
        'x-google-marketplace': {
            'type': 'GENERATED_PASSWORD'
        }
    }))

  def test_defaults_bad_type(self):
    self.assertRaises(
        config_helper.InvalidSchema, lambda: config_helper.Schema.load_yaml("""
            properties:
              p1:
                type: string
                default: 10
            """))

  def test_service_account(self):
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
                - type: ClusterRole
                  rulesType: PREDEFINED
                  rulesFromRoleName: admin
                - type: Role
                  rulesType: PREDEFINED
                  rulesFromRoleName: edit
                - type: Role
                  rulesType: PREDEFINED
                  rulesFromRoleName: view
                - type: ClusterRole
                  rulesType: CUSTOM
                  rules:
                  - apiGroups: ['v1']
                    resources: ['Secret']
                    verbs: ['*']
                  - apiGroups: ['v1']
                    resources: ['ConfigMap']
                    verbs: ['*']
                - type: Role
                  rulesType: CUSTOM
                  rules:
                  - apiGroups: ['apps/v1']
                    resources: ['Deployment']
                    verbs: ['*']
                  - apiGroups: ['']
                    resources: ['Pods']
                    verbs: ['*']
                  - apiGroups: ['apps/v1']
                    resources: ['StatefulSet']
                    verbs: ['*']
        """)
    sa = schema.properties['sa'].service_account
    self.assertIsNotNone(sa)
    self.assertListEqual(['cluster-admin', 'admin'],
                         sa.predefined_cluster_roles())
    self.assertListEqual(['edit', 'view'], sa.predefined_roles())
    self.assertListEqual([[
        {
            'apiGroups': ['v1'],
            'resources': ['Secret'],
            'verbs': ['*']
        },
        {
            'apiGroups': ['v1'],
            'resources': ['ConfigMap'],
            'verbs': ['*']
        },
    ]], sa.custom_cluster_role_rules())
    self.assertListEqual([[
        {
            'apiGroups': ['apps/v1'],
            'resources': ['Deployment'],
            'verbs': ['*']
        },
        {
            'apiGroups': [''],
            'resources': ['Pods'],
            'verbs': ['*']
        },
        {
            'apiGroups': ['apps/v1'],
            'resources': ['StatefulSet'],
            'verbs': ['*']
        },
    ]], sa.custom_role_rules())

  def test_service_account_missing_description_enforced_validate(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          sa:
            type: string
            description: unused property description
            x-google-marketplace:
              type: SERVICE_ACCOUNT
              serviceAccount:
                # required description goes here
                roles:
                - type: ClusterRole
                  rulesType: PREDEFINED
                  rulesFromRoleName: view
        """)
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'must have a `description`'):
      schema.validate()

  def test_deployer_service_account_missing_description_enforced_validate(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
            recommended: true

          images: {}

          deployerServiceAccount:
            # required description goes here
            roles:
            - type: Role
              rulesType: PREDEFINED
              rulesFromRoleName: view
        properties:
          simple:
            type: string
        """)
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'must have a `description`'):
      schema.validate()

  def test_deployer_service_account_cluster_scoped_write_predefined_role_enforced_validate(
      self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
            recommended: true

          images: {}

          deployerServiceAccount:
            description: >
              Asks for vague cluster-scoped permissions which is disallowed
            roles:
            - type: ClusterRole
              rulesType: PREDEFINED
              rulesFromRoleName: edit
        properties:
          simple:
            type: string
        """)
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Disallowed deployerServiceAccount role'):
      schema.validate()

  def test_deployer_service_account_cluster_scoped_mock_cluster_admin_role_enforced_validate(
      self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
            recommended: true

          images: {}

          deployerServiceAccount:
            description: >
              Asks for vague cluster-scoped permissions which is disallowed
            roles:
            - type: ClusterRole
              rulesType: CUSTOM
              rules:
              - apiGroups: ['*']
                resources: ['*']
                verbs: ['*']
        properties:
          simple:
            type: string
        """)
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Disallowed deployerServiceAccount role'):
      schema.validate()

  def test_deployer_service_account_no_escalated_permissions_allowed_validate(
      self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
            recommended: true

          images: {}

          deployerServiceAccount:
            description: >
              Asks for vague namespaced permissions which is allowed
            roles:
            - type: Role
              rulesType: PREDEFINED
              rulesFromRoleName: edit
        properties:
          simple:
            type: string
        """)
    schema.validate()

  def test_service_account_missing_rulesType(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'rulesType must be one of PREDEFINED or CUSTOM'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesFromRoleName: view
          """)

  def test_service_account_predefined_rules(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'rules can only be used with rulesType CUSTOM'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: PREDEFINED
                    rules:
                    - apiGroups: ['']
                      resources: ['Deployment']
                      verbs: ['*']
          """)

  def test_service_account_predefined_missing_rulesFromRoleName(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'Missing rulesFromRoleName for PREDEFINED role'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: PREDEFINED
          """)

  def test_service_account_custom_rulesFromRoleName(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'rulesFromRoleName can only be used with rulesType PREDEFINED'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: CUSTOM
                    rulesFromRoleName: edit
          """)

  def test_service_account_custom_nonResourceAttributes(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'Only attributes for resourceRules are supported in rules'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: CUSTOM
                    rules:
                    - nonResourceURLs: ['/version', '/healthz']
                      verbs: ["get"]
          """)

  def test_service_account_custom_missingRules(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Missing rules for CUSTOM role'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: CUSTOM
          """)

  def test_service_account_custom_missing_apiGroups(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                r'^Missing apiGroups in rules. Did you mean'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: CUSTOM
                    rules:
                    - resources: ['Pods']
                      verbs: ['*']
          """)

  def test_service_account_custom_empty_resources(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Missing or empty resources in rules'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: CUSTOM
                    rules:
                    - apiGroups: ['v1']
                      resources: ['']
                      verbs: ['*']
          """)

  def test_service_account_custom_empty_verbs(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Missing or empty verbs in rules'):
      config_helper.Schema.load_yaml("""
          properties:
            sa:
              type: string
              x-google-marketplace:
                type: SERVICE_ACCOUNT
                serviceAccount:
                  roles:
                  - type: Role
                    rulesType: CUSTOM
                    rules:
                    - apiGroups: ['v1']
                      resources: ['Pods']
                      verbs: ['']
          """)

  def test_storage_class(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          sc:
            type: string
            x-google-marketplace:
              type: STORAGE_CLASS
              storageClass:
                type: SSD
        """)
    self.assertIsNotNone(schema.properties['sc'].storage_class)
    sc = schema.properties['sc'].storage_class
    self.assertTrue(sc.ssd)

  def test_xstring_base64(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          s:
            type: string
            x-google-marketplace:
              type: STRING
              string:
                generatedProperties:
                  base64Encoded: s.encoded
        """)
    xstring = schema.properties['s'].string
    self.assertIsNotNone(xstring)
    self.assertEqual('s.encoded', xstring.base64_encoded)

  def test_reporting_secret(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          rs:
            type: string
            x-google-marketplace:
              type: REPORTING_SECRET
        """)
    self.assertIsNotNone(schema.properties['rs'].reporting_secret)

  def test_unknown_type(self):
    self.assertRaises(
        config_helper.InvalidSchema, lambda: config_helper.Schema.load_yaml("""
            properties:
              unk:
                type: string
                x-google-marketplace:
                  type: UNKNOWN
            """))

  def test_partner_and_solution_ids(self):
    schema_yaml = """
        x-google-marketplace:
          schemaVersion: v2
          partnerId: partner-a
          applicationApiVersion: v1beta1
          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
          images: {}
        properties: {}
        """
    self.assertRaisesRegex(
        config_helper.InvalidSchema,
        r'x-google-marketplace.partnerId and x-google-marketplace.solutionId.*',
        lambda: config_helper.Schema.load_yaml(schema_yaml))

    schema_yaml = """
        x-google-marketplace:
          schemaVersion: v2
          solutionId: solution-a
          applicationApiVersion: v1beta1
          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
          images: {}
        properties: {}
        """
    self.assertRaisesRegex(
        config_helper.InvalidSchema,
        r'x-google-marketplace.partnerId and x-google-marketplace.solutionId.*',
        lambda: config_helper.Schema.load_yaml(schema_yaml))

    schema_yaml = """
        x-google-marketplace:
          schemaVersion: v2
          partnerId: partner-a
          solutionId: solution-a
          applicationApiVersion: v1beta1
          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
          images: {}
        properties: {}
        """
    schema = config_helper.Schema.load_yaml(schema_yaml)
    self.assertEqual('partner-a', schema.x_google_marketplace.partner_id)
    self.assertEqual('solution-a', schema.x_google_marketplace.solution_id)

  def test_image_properties_are_not_allowed_in_v2(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
          images:
            main:
              properties:
                main.image:
                  type: FULL
        properties:
          image:
            type: string
            default: gcr.io/a/b:1.0
            x-google-marketplace:
              type: IMAGE
        """)
    self.assertRaisesRegex(config_helper.InvalidSchema,
                           r'.*x-google-marketplace.type=IMAGE.*',
                           lambda: schema.validate())

  def test_v2_fields(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2

          applicationApiVersion: v1beta1

          publishedVersion: 6.5.130-metadata
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
    schema.validate()
    self.assertTrue(schema.x_google_marketplace.is_v2())
    self.assertEqual(schema.x_google_marketplace.app_api_version, 'v1beta1')

    self.assertEqual(schema.x_google_marketplace.published_version,
                     '6.5.130-metadata')
    version_meta = schema.x_google_marketplace.published_version_meta
    self.assertEqual(version_meta.release_note, 'Bug fixes')
    self.assertListEqual(version_meta.release_types, ['BUG_FIX'])
    self.assertTrue(version_meta.recommended)

    images = schema.x_google_marketplace.images
    self.assertTrue(isinstance(images, dict))
    self.assertEqual(len(images), 2)
    self.assertEqual(images['main'].name, 'main')
    self.assertEqual(len(images['main'].properties), 1)
    self.assertEqual(images['main'].properties['main.image'].name, 'main.image')
    self.assertEqual(images['main'].properties['main.image'].part_type, 'FULL')
    self.assertEqual(images['db'].name, 'db')
    self.assertEqual(len(images['db'].properties), 2)
    self.assertEqual(images['db'].properties['db.image.repo'].name,
                     'db.image.repo')
    self.assertEqual(images['db'].properties['db.image.repo'].part_type,
                     'REPO_WITH_REGISTRY')
    self.assertEqual(images['db'].properties['db.image.tag'].name,
                     'db.image.tag')
    self.assertEqual(images['db'].properties['db.image.tag'].part_type, 'TAG')

    self.assertEqual(schema.x_google_marketplace.managed_updates.kalm_supported,
                     True)

  def test_publishedVersion_semver(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Invalid schema publishedVersion "6.5"'):
      config_helper.Schema.load_yaml("""
          x-google-marketplace:
            schemaVersion: v2
            applicationApiVersion: v1beta1

            publishedVersion: '6.5'
            publishedVersionMetadata:
              releaseNote: Bug fixes
            images:
              main:
                properties:
                  main.image:
                    type: FULL
          properties:
            simple:
              type: string
          """)

  def test_k8s_version_constraint(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          simple:
            type: string
        x-google-marketplace:
          clusterConstraints:
            k8sVersion: '>1.11'
        """)
    schema.validate()
    self.assertEqual(
        schema.x_google_marketplace.cluster_constraints.k8s_version, '>1.11')

  def test_resource_constraints(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          simple:
            type: string
        x-google-marketplace:
          clusterConstraints:
            resources:
            - replicas: 3
              requests:
                cpu: 100m
                memory: 512Gi
              affinity:
                simpleNodeAffinity:
                  type: REQUIRE_ONE_NODE_PER_REPLICA
            - replicas: 5
              requests:
                cpu: 50m
              affinity:
                simpleNodeAffinity:
                  type: REQUIRE_MINIMUM_NODE_COUNT
                  minimumNodeCount: 4
            - requests:
                gpu:
                  nvidia.com/gpu:
                    limits: 2
                    platforms:
                    - nvidia-tesla-k80
                    - nvidia-tesla-k100
        """)
    schema.validate()
    resources = schema.x_google_marketplace.cluster_constraints.resources
    self.assertTrue(isinstance(resources, list))
    self.assertEqual(len(resources), 3)

    self.assertEqual(resources[0].replicas, 3)
    self.assertEqual(resources[0].requests.cpu, '100m')
    self.assertEqual(resources[0].requests.memory, '512Gi')
    self.assertEqual(resources[0].affinity.simple_node_affinity.affinity_type,
                     'REQUIRE_ONE_NODE_PER_REPLICA')
    self.assertIsNone(
        resources[0].affinity.simple_node_affinity.minimum_node_count)
    self.assertEqual(resources[1].replicas, 5)
    self.assertEqual(resources[1].requests.cpu, '50m')
    self.assertEqual(resources[1].affinity.simple_node_affinity.affinity_type,
                     'REQUIRE_MINIMUM_NODE_COUNT')
    self.assertEqual(
        resources[1].affinity.simple_node_affinity.minimum_node_count, 4)

    self.assertEqual(len(resources[2].requests.gpu), 1)
    self.assertEqual(resources[2].requests.gpu['nvidia.com/gpu'].limits, 2)
    self.assertEqual(resources[2].requests.gpu['nvidia.com/gpu'].platforms,
                     ['nvidia-tesla-k80', 'nvidia-tesla-k100'])

  def test_resource_constraints_resources_not_list_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'resources must be a list'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
                replicas: 2
          """)

  def test_resource_constraints_missing_requests_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'must specify requests'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - replicas: 2
          """)

  def test_resource_constraints_empty_requests_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'must specify at least one of cpu'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - replicas: 2
                requests: {}
          """)

  def test_resource_constraints_gpu_and_other_requests_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'must not specify cpu'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  cpu: 200m
                  gpu:
                    nvidia.com/gpu: {}
          """)

  def test_resource_constraints_multiple_gpu_constraints_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'one request may include GPUs'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  gpu:
                    nvidia.com/gpu:
                      limits: 2
              - requests:
                  gpu:
                    nvidia.com/gpu: {}
          """)

  def test_resource_constraints_gpu_affinity_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Affinity unsupported for GPU'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  gpu:
                    nvidia.com/gpu: {}
                affinity:
                  simpleNodeAffinity:
                    type: REQUIRE_MINIMUM_NODE_COUNT
                    minimumNodeCount: 2
          """)

  def test_resource_constraints_gpu_replicas_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Replicas unsupported for GPU'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  gpu:
                    nvidia.com/gpu: {}
                replicas: 2
          """)

  def test_resource_constraints_gpu_not_map_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema, 'must be a map'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  gpu: []
          """)

  def test_resource_constraints_gpu_empty_requests_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'GPU requests map must contain'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  gpu: {}
          """)

  def test_resource_constraints_gpu_unrecognized_provider_invalid(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'Unsupported GPU provider'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              resources:
              - requests:
                  gpu:
                    amd.com/gpu: {}
          """)

  def test_assisted_cluster_creation_disabled(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        x-google-marketplace:
          clusterConstraints:
            assistedClusterCreation:
              type: DISABLED
              creationGuidance: "Please use existing cluster with GPU."
        """)
    schema.validate()
    assistedClusterCreation = schema.x_google_marketplace.cluster_constraints.assistedClusterCreation

    self.assertEqual(assistedClusterCreation.type, "DISABLED")
    self.assertEqual(assistedClusterCreation._creation_guidance,
                     'Please use existing cluster with GPU.')

  def test_assisted_cluster_creation_strict_custom_vm(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        x-google-marketplace:
          clusterConstraints:
            assistedClusterCreation:
              type: STRICT
              gke:
                nodePool:
                - numNodes: 2
                  machineType: custom-2-12288
        """)
    schema.validate()
    assistedClusterCreation = schema.x_google_marketplace.cluster_constraints.assistedClusterCreation

    self.assertEqual(assistedClusterCreation.type, "STRICT")
    node_pool = assistedClusterCreation.gke.node_pool
    self.assertTrue(isinstance(node_pool, list))
    self.assertEqual(len(node_pool), 1)

    self.assertEqual(node_pool[0].num_nodes, 2)
    self.assertEqual(node_pool[0].machine_type, 'custom-2-12288')

  def test_assisted_cluster_creation_strict_standard_vm(self):
    schema = config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          x-google-marketplace:
            clusterConstraints:
              assistedClusterCreation:
                type: STRICT
                gke:
                  nodePool:
                  - numNodes: 1
                    machineType: n1-standard-1
          """)
    schema.validate()
    assistedClusterCreation = schema.x_google_marketplace.cluster_constraints.assistedClusterCreation

    self.assertEqual(assistedClusterCreation.type, "STRICT")
    node_pool = assistedClusterCreation.gke.node_pool
    self.assertTrue(isinstance(node_pool, list))
    self.assertEqual(len(node_pool), 1)

    self.assertEqual(node_pool[0].num_nodes, 1)
    self.assertEqual(node_pool[0].machine_type, 'n1-standard-1')

  def test_assisted_cluster_creation_disabled_missing_guidance(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'assistedClusterCreation.creationGuidance must be specified when assistedClusterCreation.type is DISABLED'
    ):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          x-google-marketplace:
            clusterConstraints:
              assistedClusterCreation:
                type: DISABLED
          """)

  def test_assisted_cluster_creation_strict_missing_gke(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'assistedClusterCreation.gke must be specified when assistedClusterCreation.type is STRICT'
    ):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          x-google-marketplace:
            clusterConstraints:
              assistedClusterCreation:
                type: STRICT
          """)

  def test_assisted_cluster_creation_strict_too_many_nodepool(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                'gke.nodePool supports exactly one nodePool'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          x-google-marketplace:
            clusterConstraints:
              assistedClusterCreation:
                type: STRICT
                gke:
                  nodePool:
                  - numNodes: 2
                    machineType: n1-standard-1
                  - numNodes: 4
                    machineType: n2-standard-2
          """)

  def test_assisted_cluster_creation_strict_custom_vm_odd_cpu(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        'Number of cores for machineType could either be 1 or an even number'):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          x-google-marketplace:
            clusterConstraints:
              assistedClusterCreation:
                type: STRICT
                gke:
                  nodePool:
                  - numNodes: 2
                    machineType: n2-custom-3-1224
          """)

  def test_istio_valid_type(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          simple:
            type: string
        x-google-marketplace:
          clusterConstraints:
            istio:
              type: OPTIONAL
        """)
    schema.validate()
    self.assertEqual(schema.x_google_marketplace.cluster_constraints.istio.type,
                     "OPTIONAL")

  def test_istio_invalid_type(self):
    with self.assertRaisesRegex(config_helper.InvalidSchema,
                                "Invalid type of istio constraint"):
      config_helper.Schema.load_yaml("""
          applicationApiVersion: v1beta1
          properties:
            simple:
              type: string
          x-google-marketplace:
            clusterConstraints:
              istio:
                type: INVALID_TYPE
          """)

  def test_required_oauth_scopes_valid(self):
    schema = config_helper.Schema.load_yaml("""
      applicationApiVersion: v1beta1
      properties:
        simple:
          type: string
      x-google-marketplace:
        clusterConstraints:
          gcp:
            nodes:
              requiredOauthScopes:
              - https://www.googleapis.com/auth/cloud-platform
      """)
    schema.validate()
    self.assertEqual(
        schema.x_google_marketplace.cluster_constraints.gcp.nodes
        .required_oauth_scopes,
        ["https://www.googleapis.com/auth/cloud-platform"])

  def test_required_oauth_scopes_invalid_scope(self):
    with self.assertRaisesRegex(
        config_helper.InvalidSchema,
        "OAuth scope references must be fully-qualified"):
      config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          simple:
            type: string
        x-google-marketplace:
          clusterConstraints:
            gcp:
              nodes:
                requiredOauthScopes:
                - cloud-platform
        """)

  def test_deployer_service_account(self):
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
            - type: ClusterRole
              rulesType: PREDEFINED
              rulesFromRoleName: admin
            - type: Role
              rulesType: PREDEFINED
              rulesFromRoleName: edit
            - type: Role
              rulesType: PREDEFINED
              rulesFromRoleName: view
            - type: ClusterRole
              rulesType: CUSTOM
              rules:
              - apiGroups: ['v1']
                resources: ['Secret']
                verbs: ['*']
              - apiGroups: ['v1']
                resources: ['ConfigMap']
                verbs: ['*']
            - type: Role
              rulesType: CUSTOM
              rules:
              - apiGroups: ['apps/v1']
                resources: ['Deployment']
                verbs: ['*']
              - apiGroups: ['apps/v1']
                resources: ['StatefulSet']
                verbs: ['*']
        properties:
          simple:
            type: string
      """)
    dsa = schema.x_google_marketplace.deployer_service_account
    self.assertIsNotNone(dsa)
    self.assertListEqual(['cluster-admin', 'admin'],
                         dsa.predefined_cluster_roles())
    self.assertListEqual(['edit', 'view'], dsa.predefined_roles())
    self.assertListEqual([[
        {
            'apiGroups': ['v1'],
            'resources': ['Secret'],
            'verbs': ['*']
        },
        {
            'apiGroups': ['v1'],
            'resources': ['ConfigMap'],
            'verbs': ['*']
        },
    ]], dsa.custom_cluster_role_rules())
    self.assertListEqual([[
        {
            'apiGroups': ['apps/v1'],
            'resources': ['Deployment'],
            'verbs': ['*']
        },
        {
            'apiGroups': ['apps/v1'],
            'resources': ['StatefulSet'],
            'verbs': ['*']
        },
    ]], dsa.custom_role_rules())

  def test_validate_good(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          simple:
            type: string
        """)
    schema.validate()

  def test_app_api_version_alternative_names(self):
    schema = config_helper.Schema.load_yaml("""
        applicationApiVersion: v1beta1
        properties:
          simple:
            type: string
        """)
    schema.validate()
    self.assertEqual(schema.app_api_version, 'v1beta1')

    schema = config_helper.Schema.load_yaml("""
        application_api_version: v1beta1
        properties:
          simple:
            type: string
        """)
    schema.validate()
    self.assertEqual(schema.app_api_version, 'v1beta1')

  def test_validate_missing_app_api_version(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, 'applicationApiVersion',
        lambda: config_helper.Schema.load_yaml("""
            properties:
              simple:
                type: string
            """).validate())

  def test_validate_bad_form_too_many_items(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, 'form',
        lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - widget: help
              description: My arbitrary <i>description</i>
            - widget: help
              description: My arbitrary <i>description</i>
            """).validate())

  def test_validate_bad_form_missing_type(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, 'form',
        lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - description: My arbitrary <i>description</i>
            """).validate())

  def test_validate_bad_form_unrecognized_type(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, 'form',
        lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - widget: magical
              description: My arbitrary <i>description</i>
            """).validate())

  def test_validate_bad_form_missing_description(self):
    self.assertRaisesRegex(
        config_helper.InvalidSchema, 'form',
        lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - widget: help
            """).validate())

  def test_read_values_to_dict(self):
    dirname = tempfile.mkdtemp()
    with open(os.path.join(dirname, "file1"), "w") as stream:
      stream.write("value1")
    with open(os.path.join(dirname, "file2"), "w") as stream:
      stream.write("2")

    schema = """
    properties:
      key1:
        type: string
      key2:
        type: number
    """
    expected_values = {"file1": u"value1", "file2": u"2"}
    actual_values = config_helper._read_values_to_dict(
        dirname, config_helper.Schema.load_yaml(schema))
    self.assertEqual(actual_values, expected_values)


if __name__ == 'main':
  unittest.main()
