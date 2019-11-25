#!/usr/bin/env python2
#
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

import collections
import io
import os
import re
import sys

import yaml

NAME_RE = re.compile(r'[a-zA-z0-9_\.\-]+$')
# Suggested from https://semver.org
SEMVER_RE = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
                       '(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
                       '(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
                       '(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')

XGOOGLE = 'x-google-marketplace'
XTYPE_NAME = 'NAME'
XTYPE_NAMESPACE = 'NAMESPACE'
XTYPE_IMAGE = 'IMAGE'
XTYPE_DEPLOYER_IMAGE = 'DEPLOYER_IMAGE'
XTYPE_PASSWORD = 'GENERATED_PASSWORD'
XTYPE_REPORTING_SECRET = 'REPORTING_SECRET'
XTYPE_SERVICE_ACCOUNT = 'SERVICE_ACCOUNT'
XTYPE_STORAGE_CLASS = 'STORAGE_CLASS'
XTYPE_STRING = 'STRING'
XTYPE_APPLICATION_UID = 'APPLICATION_UID'
XTYPE_ISTIO_ENABLED = 'ISTIO_ENABLED'
XTYPE_INGRESS_AVAILABLE = 'INGRESS_AVAILABLE'
XTYPE_TLS_CERTIFICATE = 'TLS_CERTIFICATE'
XTYPE_MASKED_FIELD = 'MASKED_FIELD'

WIDGET_TYPES = ['help']

_OAUTH_SCOPE_PREFIX = 'https://www.googleapis.com/auth/'


class InvalidName(Exception):
  pass


class InvalidValue(Exception):
  pass


class InvalidSchema(Exception):
  pass


def load_values(values_file, values_dir, schema):
  if values_file == '-':
    return yaml.safe_load(sys.stdin.read())
  if values_file and os.path.isfile(values_file):
    with open(values_file, 'r') as f:
      return yaml.safe_load(f.read())
  return _read_values_to_dict(values_dir, schema)


def _read_values_to_dict(values_dir, schema):
  """Returns a dict constructed from files in values_dir."""
  files = [
      f for f in os.listdir(values_dir)
      if os.path.isfile(os.path.join(values_dir, f))
  ]
  result = {}
  for filename in files:
    if not NAME_RE.match(filename):
      raise InvalidName('Invalid config parameter name: {}'.format(filename))
    file_path = os.path.join(values_dir, filename)
    with open(file_path, "r") as f:
      data = f.read().decode('utf-8')
      result[filename] = data

  # Data read in as strings. Convert them to proper types defined in schema.
  result = {
      k: schema.properties[k].str_to_type(v) if k in schema.properties else v
      for k, v in result.iteritems()
  }
  return result


class Schema:
  """Accesses a JSON schema."""

  @staticmethod
  def load_yaml_file(filepath):
    with io.open(filepath, 'r') as f:
      d = yaml.load(f)
      return Schema(d)

  @staticmethod
  def load_yaml(yaml_str):
    return Schema(yaml.load(yaml_str))

  def __init__(self, dictionary):
    self._x_google_marketplace = _maybe_get_and_apply(
        dictionary, 'x-google-marketplace',
        lambda v: SchemaXGoogleMarketplace(v))

    self._required = dictionary.get('required', [])
    self._properties = {
        k: SchemaProperty(k, v, k in self._required)
        for k, v in dictionary.get('properties', {}).iteritems()
    }

    self._app_api_version = dictionary.get(
        'applicationApiVersion', dictionary.get('application_api_version',
                                                None))

    self._form = dictionary.get('form', [])

  def validate(self):
    """Fully validates the schema, raising InvalidSchema if fails."""
    bad_required_names = [
        x for x in self._required if x not in self._properties
    ]
    if bad_required_names:
      raise InvalidSchema(
          'Undefined property names found in required: {}'.format(
              ', '.join(bad_required_names)))

    is_v2 = False
    if self._x_google_marketplace is not None:
      self._x_google_marketplace.validate()
      is_v2 = self._x_google_marketplace.is_v2()

    if not is_v2 and self._app_api_version is None:
      raise InvalidSchema('applicationApiVersion is required')

    if len(self.form) > 1:
      raise InvalidSchema('form must not contain more than 1 item.')

    for item in self.form:
      if 'widget' not in item:
        raise InvalidSchema('form items must have a widget.')
      if item['widget'] not in WIDGET_TYPES:
        raise InvalidSchema('Unrecognized form widget: {}'.format(
            item['widget']))
      if 'description' not in item:
        raise InvalidSchema('form items must have a description.')

  @property
  def x_google_marketplace(self):
    return self._x_google_marketplace

  @property
  def app_api_version(self):
    if self.is_v2():
      return self.x_google_marketplace.app_api_version
    return self._app_api_version

  @property
  def properties(self):
    return self._properties

  @property
  def required(self):
    return self._required

  @property
  def form(self):
    return self._form

  def properties_matching(self, definition):
    return [
        v for k, v in self._properties.iteritems()
        if v.matches_definition(definition)
    ]

  def is_v2(self):
    if self.x_google_marketplace:
      return self.x_google_marketplace.is_v2()
    return False


_SCHEMA_VERSION_1 = 'v1'
_SCHEMA_VERSION_2 = 'v2'
_SCHEMA_VERSIONS = [_SCHEMA_VERSION_1, _SCHEMA_VERSION_2]


class SchemaXGoogleMarketplace:
  """Accesses the top level x-google-markplace."""

  def __init__(self, dictionary):
    self._app_api_version = None
    self._published_version = None
    self._published_version_meta = None
    self._images = None
    self._cluster_constraints = None
    self._deployer_service_account = None

    self._schema_version = dictionary.get('schemaVersion', _SCHEMA_VERSION_1)
    if self._schema_version not in _SCHEMA_VERSIONS:
      raise InvalidSchema('Invalid schema version {}'.format(
          self._schema_version))

    if 'clusterConstraints' in dictionary:
      self._cluster_constraints = SchemaClusterConstraints(
          dictionary['clusterConstraints'])

    if not self.is_v2():
      return

    self._app_api_version = _must_get(
        dictionary, 'applicationApiVersion',
        'x-google-marketplace.applicationApiVersion is required')
    self._published_version = _must_get(
        dictionary, 'publishedVersion',
        'x-google-marketplace.publishedVersion is required')
    if not SEMVER_RE.match(self._published_version):
      raise InvalidSchema(
          'Invalid schema publishedVersion "{}"; must be semver including patch version'
          .format(self._published_version))
    self._published_version_meta = _must_get_and_apply(
        dictionary, 'publishedVersionMetadata', lambda v: SchemaVersionMeta(v),
        'x-google-marketplace.publishedVersionMetadata is required')

    self._managed_updates = SchemaManagedUpdates(
        dictionary.get('managedUpdates', {}))

    images = _must_get(dictionary, 'images',
                       'x-google-marketplace.images is required')
    self._images = {k: SchemaImage(k, v) for k, v in images.iteritems()}

    if 'deployerServiceAccount' in dictionary:
      self._deployer_service_account = SchemaXServiceAccount(
          dictionary['deployerServiceAccount'])

  def validate(self):
    pass

  @property
  def cluster_constraints(self):
    return self._cluster_constraints

  @property
  def app_api_version(self):
    return self._app_api_version

  @property
  def published_version(self):
    return self._published_version

  @property
  def published_version_meta(self):
    return self._published_version_meta

  @property
  def images(self):
    return self._images

  @property
  def managed_updates(self):
    return self._managed_updates

  @property
  def deployer_service_account(self):
    return self._deployer_service_account

  def is_v2(self):
    return self._schema_version == _SCHEMA_VERSION_2


class SchemaManagedUpdates:
  """Accesses managedUpdates."""

  def __init__(self, dictionary):
    self._kalm_supported = dictionary.get('kalmSupported', False)

  @property
  def kalm_supported(self):
    return self._kalm_supported


class SchemaClusterConstraints:
  """Accesses top level clusterConstraints."""

  def __init__(self, dictionary):
    self._k8s_version = dictionary.get('k8sVersion', None)
    self._resources = None
    self._istio = None
    self._gcp = None

    if 'resources' in dictionary:
      resources = dictionary['resources']
      if not isinstance(resources, list):
        raise InvalidSchema('clusterConstraints.resources must be a list')
      self._resources = [SchemaResourceConstraints(r) for r in resources]

    self._istio = _maybe_get_and_apply(dictionary, 'istio',
                                       lambda v: SchemaIstio(v))
    self._gcp = _maybe_get_and_apply(dictionary, 'gcp', lambda v: SchemaGcp(v))

  @property
  def k8s_version(self):
    return self._k8s_version

  @property
  def resources(self):
    return self._resources

  @property
  def istio(self):
    return self._istio

  @property
  def gcp(self):
    return self._gcp


class SchemaResourceConstraints:
  """Accesses a single resource's constraints."""

  def __init__(self, dictionary):
    self._replicas = dictionary.get('replicas', None)
    self._affinity = _maybe_get_and_apply(
        dictionary, 'affinity', lambda v: SchemaResourceConstraintAffinity(v))
    self._requests = _maybe_get_and_apply(
        dictionary, 'requests', lambda v: SchemaResourceConstraintRequests(v))

  @property
  def replicas(self):
    return self._replicas

  @property
  def affinity(self):
    return self._affinity

  @property
  def requests(self):
    return self._requests


class SchemaResourceConstraintAffinity:
  """Accesses a single resource's affinity constraints"""

  def __init__(self, dictionary):
    self._simple_node_affinity = _maybe_get_and_apply(
        dictionary, 'simpleNodeAffinity', lambda v: SchemaSimpleNodeAffinity(v))

  @property
  def simple_node_affinity(self):
    return self._simple_node_affinity


class SchemaSimpleNodeAffinity:
  """Accesses simple node affinity for resource constraints."""

  def __init__(self, dictionary):
    self._minimum_node_count = dictionary.get('minimumNodeCount', None)
    self._type = _must_get(dictionary, 'type',
                           'simpleNodeAffinity requires a type')

    if (self._type == 'REQUIRE_MINIMUM_NODE_COUNT' and
        self._minimum_node_count is None):
      raise InvalidSchema(
          'simpleNodeAffinity of type REQUIRE_MINIMUM_NODE_COUNT '
          'requires minimumNodeCount')

  @property
  def affinity_type(self):
    return self._type

  @property
  def minimum_node_count(self):
    return self._minimum_node_count


class SchemaResourceConstraintRequests:
  """Accesses a single resource's requests."""

  def __init__(self, dictionary):
    self.cpu = dictionary.get('cpu', None)
    self.memory = dictionary.get('memory', None)

  @property
  def cpu(self):
    return self._cpu

  @property
  def memory(self):
    return self._memory


_ISTIO_TYPE_OPTIONAL = "OPTIONAL"
_ISTIO_TYPE_REQUIRED = "REQUIRED"
_ISTIO_TYPE_UNSUPPORTED = "UNSUPPORTED"
_ISTIO_TYPES = [
    _ISTIO_TYPE_OPTIONAL, _ISTIO_TYPE_REQUIRED, _ISTIO_TYPE_UNSUPPORTED
]


class SchemaIstio:
  """Accesses top level istio."""

  def __init__(self, dictionary):
    self._type = dictionary.get('type', None)
    _must_contain(self._type, _ISTIO_TYPES, "Invalid type of istio constraint")

  @property
  def type(self):
    return self._type


class SchemaGcp:
  """Accesses top level GCP constraints."""

  def __init__(self, dictionary):
    self._nodes = _maybe_get_and_apply(dictionary, 'nodes',
                                       lambda v: SchemaNodes(v))

  @property
  def nodes(self):
    return self._nodes


class SchemaNodes:
  """Accesses GKE cluster node constraints."""

  def __init__(self, dictionary):
    self._required_oauth_scopes = dictionary.get('requiredOauthScopes', [])
    if not isinstance(self._required_oauth_scopes, list):
      raise InvalidSchema('nodes.requiredOauthScopes must be a list')
    for scope in self._required_oauth_scopes:
      if not scope.startswith(_OAUTH_SCOPE_PREFIX):
        raise InvalidSchema(
            'OAuth scope references must be fully-qualified (start with {})'
            .format(_OAUTH_SCOPE_PREFIX))

  @property
  def required_oauth_scopes(self):
    return self._required_oauth_scopes


class SchemaImage:
  """Accesses an image definition."""

  def __init__(self, name, dictionary):
    self._name = name
    self._properties = {
        k: SchemaImageProjectionProperty(k, v)
        for k, v in dictionary.get('properties', {}).iteritems()
    }

  @property
  def name(self):
    return self._name

  @property
  def properties(self):
    return self._properties


IMAGE_PROJECTION_TYPE_FULL = 'FULL'
IMAGE_PROJECTION_TYPE_REPO = 'REPO_WITHOUT_REGISTRY'
IMAGE_PROJECTION_TYPE_REGISTRY_REPO = 'REPO_WITH_REGISTRY'
IMAGE_PROJECTION_TYPE_REGISTRY = 'REGISTRY'
IMAGE_PROJECTION_TYPE_TAG = 'TAG'
_IMAGE_PROJECTION_TYPES = [
    IMAGE_PROJECTION_TYPE_FULL,
    IMAGE_PROJECTION_TYPE_REPO,
    IMAGE_PROJECTION_TYPE_REGISTRY_REPO,
    IMAGE_PROJECTION_TYPE_REGISTRY,
    IMAGE_PROJECTION_TYPE_TAG,
]


class SchemaImageProjectionProperty:
  """Accesses a property that an image name projects to."""

  def __init__(self, name, dictionary):
    self._name = name
    self._type = _must_get(
        dictionary, 'type',
        'Each property for an image in x-google-marketplace.images '
        'must have a valid type')
    if self._type not in _IMAGE_PROJECTION_TYPES:
      raise InvalidSchema('image property {} has invalid type {}'.format(
          name, self._type))

  @property
  def name(self):
    return self._name

  @property
  def part_type(self):
    return self._type


class SchemaVersionMeta:
  """Accesses publishedVersionMetadata."""

  def __init__(self, dictionary):
    self._recommended = dictionary.get('recommended', False)
    self._release_types = dictionary.get('releaseTypes', [])
    self._release_note = _must_get(
        dictionary, 'releaseNote',
        'publishedVersionMetadata.releaseNote is required')

  @property
  def recommended(self):
    return self._recommended

  @property
  def release_note(self):
    return self._release_note

  @property
  def release_types(self):
    return self._release_types


class SchemaProperty:
  """Accesses a JSON schema property."""

  def __init__(self, name, dictionary, required):
    self._name = name
    self._d = dictionary
    self._required = required
    self._default = dictionary.get('default', None)
    self._x = dictionary.get(XGOOGLE, None)
    self._application_uid = None
    self._image = None
    self._password = None
    self._reporting_secret = None
    self._service_account = None
    self._storage_class = None
    self._string = None
    self._tls_certificate = None

    if not NAME_RE.match(name):
      raise InvalidSchema('Invalid property name: {}'.format(name))

    self._type = _must_get_and_apply(
        dictionary, 'type', lambda v: {
            'int': int,
            'integer': int,
            'string': str,
            'number': float,
            'boolean': bool,
        }.get(v, None), 'Property {} has no type'.format(name))

    if not self._type:
      raise InvalidSchema('Property {} has unsupported type: {}'.format(
          name, dictionary['type']))

    if self._default:
      if not isinstance(self._default, self._type):
        raise InvalidSchema(
            'Property {} has a default value of invalid type'.format(name))

    if self._x:
      xt = _must_get(self._x, 'type',
                     'Property {} has {} without a type'.format(name, XGOOGLE))

      if xt in (XTYPE_NAME, XTYPE_NAMESPACE, XTYPE_DEPLOYER_IMAGE,
                XTYPE_MASKED_FIELD):
        _property_must_have_type(self, str)
      elif xt in (XTYPE_ISTIO_ENABLED, XTYPE_INGRESS_AVAILABLE):
        _property_must_have_type(self, bool)
      elif xt == XTYPE_APPLICATION_UID:
        _property_must_have_type(self, str)
        d = self._x.get('applicationUid', {})
        self._application_uid = SchemaXApplicationUid(d)
      elif xt == XTYPE_IMAGE:
        _property_must_have_type(self, str)
        d = self._x.get('image', {})
        self._image = SchemaXImage(d, self._default)
      elif xt == XTYPE_PASSWORD:
        _property_must_have_type(self, str)
        d = self._x.get('generatedPassword', {})
        spec = {
            'length': d.get('length', 10),
            'include_symbols': d.get('includeSymbols', False),
            'base64': d.get('base64', True),
        }
        self._password = SchemaXPassword(**spec)
      elif xt == XTYPE_SERVICE_ACCOUNT:
        _property_must_have_type(self, str)
        d = self._x.get('serviceAccount', {})
        self._service_account = SchemaXServiceAccount(d)
      elif xt == XTYPE_STORAGE_CLASS:
        _property_must_have_type(self, str)
        d = self._x.get('storageClass', {})
        self._storage_class = SchemaXStorageClass(d)
      elif xt == XTYPE_STRING:
        _property_must_have_type(self, str)
        d = self._x.get('string', {})
        self._string = SchemaXString(d)
      elif xt == XTYPE_REPORTING_SECRET:
        _property_must_have_type(self, str)
        d = self._x.get('reportingSecret', {})
        self._reporting_secret = SchemaXReportingSecret(d)
      elif xt == XTYPE_TLS_CERTIFICATE:
        _property_must_have_type(self, str)
        d = self._x.get('tlsCertificate', {})
        self._tls_certificate = SchemaXTlsCertificate(d)
      else:
        raise InvalidSchema('Property {} has an unknown type: {}'.format(
            name, xt))

  @property
  def name(self):
    return self._name

  @property
  def required(self):
    return self._required

  @property
  def default(self):
    return self._default

  @property
  def type(self):
    """Python type of the property."""
    return self._type

  @property
  def xtype(self):
    if self._x:
      return self._x['type']
    return None

  @property
  def application_uid(self):
    return self._application_uid

  @property
  def image(self):
    return self._image

  @property
  def password(self):
    return self._password

  @property
  def reporting_secret(self):
    return self._reporting_secret

  @property
  def service_account(self):
    return self._service_account

  @property
  def storage_class(self):
    return self._storage_class

  @property
  def string(self):
    return self._string

  @property
  def tls_certificate(self):
    return self._tls_certificate

  def str_to_type(self, str_val):
    if self._type == bool:
      if str_val in {'true', 'True', 'yes', 'Yes'}:
        return True
      elif str_val in {'false', 'False', 'no', 'No'}:
        return False
      else:
        raise InvalidValue('Bad value for boolean property {}: {}'.format(
            self._name, str_val))
    return self._type(str_val)

  def matches_definition(self, definition):
    """Returns true of the definition partially matches.

    The definition argument is a dictionary. All fields in the hierarchy
    defined there must be present and have the same values in the schema
    in order for the property to be a match.

    There is a special `name` field in the dictionary that captures the
    property name, which does not originally exist in the schema.
    """

    def _matches(dictionary, subdict):
      for k, sv in subdict.iteritems():
        v = dictionary.get(k, None)
        if isinstance(v, dict):
          if not _matches(v, sv):
            return False
        else:
          if v != sv:
            return False
      return True

    return _matches(
        dict(list(self._d.iteritems()) + [('name', self._name)]), definition)

  def __eq__(self, other):
    if not isinstance(other, SchemaProperty):
      return False
    return other._name == self._name and other._d == self._d


class SchemaXApplicationUid:
  """Accesses APPLICATION_UID properties."""

  def __init__(self, dictionary):
    generated_properties = dictionary.get('generatedProperties', {})
    self._application_create = generated_properties.get(
        'createApplicationBoolean', None)

  @property
  def application_create(self):
    return self._application_create


class SchemaXImage:
  """Accesses IMAGE and DEPLOYER_IMAGE properties."""

  def __init__(self, dictionary, default):
    self._split_by_colon = None
    self._split_to_registry_repo_tag = None

    if not default:
      raise InvalidSchema('default image value must be specified')
    if not default.startswith('gcr.io'):
      raise InvalidSchema(
          'default image value must state registry: {}'.format(default))
    if ':' not in default:
      raise InvalidSchema(
          'default image value is missing a tag or digest: {}'.format(default))

    generated_properties = dictionary.get('generatedProperties', {})
    if 'splitByColon' in generated_properties:
      s = generated_properties['splitByColon']
      self._split_by_colon = (
          _must_get(s, 'before',
                    '"before" attribute is required within splitByColon'),
          _must_get(s, 'after',
                    '"after" attribute is required within splitByColon'))
    if 'splitToRegistryRepoTag' in generated_properties:
      s = generated_properties['splitToRegistryRepoTag']
      parts = ['registry', 'repo', 'tag']
      self._split_to_registry_repo_tag = tuple([
          _must_get(
              s, name,
              '"{}" attribute is required within splitToRegistryRepoTag'.format(
                  name)) for name in parts
      ])

  @property
  def split_by_colon(self):
    """Return 2-tuple of before- and after-colon names, or None"""
    return self._split_by_colon

  @property
  def _split_to_registry_repo_tag(self):
    """Return 3-tuple, or None"""
    return self._split_to_registry_repo_tag


SchemaXPassword = collections.namedtuple(
    'SchemaXPassword', ['length', 'include_symbols', 'base64'])


class SchemaXServiceAccount:
  """Accesses SERVICE_ACCOUNT property."""

  def __init__(self, dictionary):
    self._roles = dictionary.get('roles', [])

  def custom_role_rules(self):
    """Returns a list of rules for custom Roles."""
    return [
        role.get('rules', [])
        for role in self._roles
        if role['type'] == 'Role' and role['rulesType'] == 'CUSTOM'
    ]

  def custom_cluster_role_rules(self):
    """Returns a list of rules for custom ClusterRoles."""
    return [
        role.get('rules', [])
        for role in self._roles
        if role['type'] == 'ClusterRole' and role['rulesType'] == 'CUSTOM'
    ]

  def predefined_roles(self):
    """Returns a list of predefined Roles."""
    return [
        role.get('rulesFromRoleName')
        for role in self._roles
        if role['type'] == 'Role' and role['rulesType'] == 'PREDEFINED'
    ]

  def predefined_cluster_roles(self):
    """Returns a list of predefined ClusterRoles."""
    return [
        role.get('rulesFromRoleName')
        for role in self._roles
        if role['type'] == 'ClusterRole' and role['rulesType'] == 'PREDEFINED'
    ]


class SchemaXStorageClass:
  """Accesses STORAGE_CLASS property."""

  def __init__(self, dictionary):
    self._type = dictionary['type']

  @property
  def ssd(self):
    return self._type == 'SSD'


class SchemaXString:
  """Accesses STRING property."""

  def __init__(self, dictionary):
    generated_properties = dictionary.get('generatedProperties', {})

    self._base64_encoded = generated_properties.get('base64Encoded', None)

  @property
  def base64_encoded(self):
    return self._base64_encoded


class SchemaXReportingSecret:
  """Accesses REPORTING_SECRET property."""

  def __init__(self, dictionary):
    pass


class SchemaXTlsCertificate:
  """Accesses TLS_CERTIFICATE property."""

  def __init__(self, dictionary):
    generated_properties = dictionary.get('generatedProperties', {})

    self._base64_encoded_private_key = generated_properties.get(
        'base64EncodedPrivateKey', None)
    self._base64_encoded_certificate = generated_properties.get(
        'base64EncodedCertificate', None)

  @property
  def base64_encoded_private_key(self):
    return self._base64_encoded_private_key

  @property
  def base64_encoded_certificate(self):
    return self._base64_encoded_certificate


def _must_get(dictionary, key, error_msg):
  """Gets the value of the key, or raises InvalidSchema."""
  if key not in dictionary:
    raise InvalidSchema(error_msg)
  return dictionary[key]


def _maybe_get_and_apply(dictionary, key, apply_fn):
  """Returns the result of apply_fn on the value of the key if not None."""
  if key not in dictionary:
    return None
  return apply_fn(dictionary[key])


def _must_get_and_apply(dictionary, key, apply_fn, error_msg):
  """Similar to _maybe_get_and_apply but raises InvalidSchema if no such key."""
  value = _must_get(dictionary, key, error_msg)
  return apply_fn(value)


def _must_contain(value, valid_list, error_msg):
  """Validates that value in valid_list, or raises InvalidSchema."""
  if value not in valid_list:
    raise InvalidSchema("{}. Must be one of {}".format(error_msg,
                                                       ', '.join(valid_list)))


def _property_must_have_type(prop, expected_type):
  if prop.type != expected_type:
    readable_type = {
        str: 'string',
        bool: 'boolean',
        int: 'integer',
        float: 'float',
    }.get(expected_type, expected_type.__name__)
    raise InvalidSchema(
        '{} x-google-marketplace type property must be of type {}'.format(
            prop.xtype, readable_type))
