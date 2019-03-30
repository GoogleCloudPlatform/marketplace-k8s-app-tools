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

import tempfile
import unittest

import config_helper

# TODO(wgrzelak): Add more tests here.

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
    default: gcr.io/google/busybox
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
      type: CERTIFICATE
      certificate:
        generatedProperties:
          base64EncodedKey: keyEncoded
          base64EncodedCrt: crtEncoded
required:
- propertyString
- propertyPassword
form:
- widget: help
  description: My arbitrary <i>description</i>
"""


class ConfigHelperTest(unittest.TestCase):

  def test_load_yaml_file(self):
    with tempfile.NamedTemporaryFile('w') as f:
      f.write(SCHEMA.encode('utf_8'))
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
    self.assertRaisesRegexp(config_helper.InvalidSchema,
                            r'propertyB, propertyC', load_and_validate,
                            schema_yaml)

  def test_types_and_defaults(self):
    schema = config_helper.Schema.load_yaml(SCHEMA)
    self.assertEqual({
        'propertyString', 'propertyStringWithDefault', 'propertyInt',
        'propertyIntWithDefault', 'propertyInteger',
        'propertyIntegerWithDefault', 'propertyNumber',
        'propertyNumberWithDefault', 'propertyBoolean',
        'propertyBooleanWithDefault', 'propertyImage', 'propertyDeployerImage',
        'propertyPassword', 'applicationUid', 'istioEnabled',
        'ingressAvailable', 'certificate'
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
    self.assertEqual('gcr.io/google/busybox',
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
    self.assertEqual('CERTIFICATE', schema.properties['certificate'].xtype)

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
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        r'.*must be of type string$', lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: integer
                x-google-marketplace:
                  type: NAME
            """))
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        r'.*must be of type string$', lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: number
                x-google-marketplace:
                  type: NAMESPACE
            """))
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        r'.*must be of type string$', lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: int
                x-google-marketplace:
                  type: DEPLOYER_IMAGE
            """))
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        r'.*must be of type string$', lambda: config_helper.Schema.load_yaml("""
            properties:
              u:
                type: boolean
                x-google-marketplace:
                  type: APPLICATION_UID
            """))
    self.assertRaisesRegexp(
        config_helper.InvalidSchema, r'.*must be of type boolean$', lambda:
        config_helper.Schema.load_yaml("""
            properties:
              u:
                type: string
                x-google-marketplace:
                  type: ISTIO_ENABLED
            """))
    self.assertRaisesRegexp(
        config_helper.InvalidSchema, r'.*must be of type boolean$', lambda:
        config_helper.Schema.load_yaml("""
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

  def test_image_type(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
            x-google-marketplace:
              type: IMAGE
        """)
    self.assertIsNotNone(schema.properties['i'].image)
    self.assertIsNone(schema.properties['i'].image.split_by_colon)
    self.assertIsNone(schema.properties['i'].image._split_to_registry_repo_tag)

  def test_image_type_splitbycolon(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          i:
            type: string
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
              type: CERTIFICATE
        """)

    self.assertIsNotNone(schema.properties['c1'].certificate)
    self.assertIsNone(schema.properties['c1'].certificate.base64_encoded_key)
    self.assertIsNone(schema.properties['c1'].certificate.base64_encoded_crt)

    schema = config_helper.Schema.load_yaml("""
        properties:
          c1:
            type: string
            x-google-marketplace:
              type: CERTIFICATE
              certificate:
                generatedProperties:
                  base64EncodedKey: c1.Base64Key
                  base64EncodedCrt: c1.Base64Crt
        """)
    self.assertIsNotNone(schema.properties['c1'].certificate)
    self.assertEqual('c1.Base64Key',
                     schema.properties['c1'].certificate.base64_encoded_key)
    self.assertEqual('c1.Base64Crt',
                     schema.properties['c1'].certificate.base64_encoded_crt)

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
    self.assertRaises(config_helper.InvalidValue, lambda: schema.properties[
        'pb'].str_to_type('bad'))

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
            'apiGroups': ['apps/v1'],
            'resources': ['StatefulSet'],
            'verbs': ['*']
        },
    ]], sa.custom_role_rules())

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

  def test_v2_fields(self):
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

    self.assertEqual(schema.x_google_marketplace.published_version, '6.5.130')
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
              affinity:
                simpleNodeAffinity:
                  type: REQUIRE_MINIMUM_NODE_COUNT
                  minimumNodeCount: 4
        """)
    schema.validate()
    resources = schema.x_google_marketplace.cluster_constraints.resources
    self.assertTrue(isinstance(resources, list))
    self.assertEqual(len(resources), 2)
    self.assertEqual(resources[0].replicas, 3)
    self.assertEqual(resources[0].requests.cpu, '100m')
    self.assertEqual(resources[0].requests.memory, '512Gi')
    self.assertEqual(resources[0].affinity.simple_node_affinity.affinity_type,
                     'REQUIRE_ONE_NODE_PER_REPLICA')
    self.assertIsNone(
        resources[0].affinity.simple_node_affinity.minimum_node_count)
    self.assertEqual(resources[1].replicas, 5)
    self.assertIsNone(resources[1].requests)
    self.assertEqual(resources[1].affinity.simple_node_affinity.affinity_type,
                     'REQUIRE_MINIMUM_NODE_COUNT')
    self.assertEqual(
        resources[1].affinity.simple_node_affinity.minimum_node_count, 4)

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
    with self.assertRaisesRegexp(config_helper.InvalidSchema,
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
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        'applicationApiVersion', lambda: config_helper.Schema.load_yaml("""
            properties:
              simple:
                type: string
            """).validate())

  def test_validate_bad_form_too_many_items(self):
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        'form', lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - widget: help
              description: My arbitrary <i>description</i>
            - widget: help
              description: My arbitrary <i>description</i>
            """).validate())

  def test_validate_bad_form_missing_type(self):
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        'form', lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - description: My arbitrary <i>description</i>
            """).validate())

  def test_validate_bad_form_unrecognized_type(self):
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        'form', lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - widget: magical
              description: My arbitrary <i>description</i>
            """).validate())

  def test_validate_bad_form_missing_description(self):
    self.assertRaisesRegexp(
        config_helper.InvalidSchema,
        'form', lambda: config_helper.Schema.load_yaml("""
            applicationApiVersion: v1beta1
            form:
            - widget: help
            """).validate())


if __name__ == 'main':
  unittest.main()
