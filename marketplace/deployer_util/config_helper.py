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

WIDGET_TYPES = ['help']


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
  """Wrapper class providing convenient access to a JSON schema."""

  @staticmethod
  def load_yaml_file(filepath):
    with io.open(filepath, 'r') as f:
      d = yaml.load(f)
      return Schema(d)

  @staticmethod
  def load_yaml(yaml_str):
    return Schema(yaml.load(yaml_str))

  def __init__(self, dictionary):
    self._required = dictionary.get('required', [])
    self._properties = {
        k: SchemaProperty(k, v, k in self._required)
        for k, v in dictionary.get('properties', {}).iteritems()
    }

    bad_required_names = [
        x for x in self._required if x not in self._properties
    ]
    if bad_required_names:
      raise InvalidSchema(
          'Undefined property names found in required: {}'.format(
              ', '.join(bad_required_names)))

    self._app_api_version = dictionary.get(
        'applicationApiVersion', dictionary.get('application_api_version',
                                                None))

    self._form = dictionary.get('form', [])

  def validate(self):
    """Fully validates the schema, raising InvalidSchema if fails."""
    if self.app_api_version is None:
      raise InvalidSchema('applicationApiVersion is required')

    if len(self.form) > 1:
      raise InvalidSchema('form must not contain more than 1 item.')

    for item in self.form:
      if 'widget' not in item:
        raise InvalidSchema('form items must have a widget.')
      if item['widget'] not in WIDGET_TYPES:
        raise InvalidSchema('Unrecognized form widget: {}', item['widget'])
      if 'description' not in item:
        raise InvalidSchema('form items must have a description.')

  @property
  def app_api_version(self):
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


class SchemaProperty:
  """Wrapper class providing convenient access to a JSON schema property."""

  def __init__(self, name, dictionary, required):
    self._name = name
    self._d = dictionary
    self._required = required
    self._default = dictionary.get('default', None)
    self._x = dictionary.get(XGOOGLE, None)
    self._image = None
    self._password = None
    self._reporting_secret = None
    self._service_account = None
    self._storage_class = None
    self._string = None

    if not NAME_RE.match(name):
      raise InvalidSchema('Invalid property name: {}'.format(name))
    if 'type' not in dictionary:
      raise InvalidSchema('Property {} has no type'.format(name))
    self._type = {
        'int': int,
        'integer': int,
        'string': str,
        'number': float,
        'boolean': bool,
    }.get(dictionary['type'], None)
    if not self._type:
      raise InvalidSchema('Property {} has unsupported type: {}'.format(
          name, dictionary['type']))

    if self._default:
      if not isinstance(self._default, self._type):
        raise InvalidSchema(
            'Property {} has a default value of invalid type'.format(name))

    if self._x:
      if 'type' not in self._x:
        raise InvalidSchema('Property {} has {} without a type'.format(
            name, XGOOGLE))
      xt = self._x['type']
      if xt in (XTYPE_NAME, XTYPE_NAMESPACE, XTYPE_APPLICATION_UID,
                XTYPE_DEPLOYER_IMAGE):
        pass
      elif xt == XTYPE_IMAGE:
        d = self._x.get('image', {})
        self._image = SchemaXImage(d)
      elif xt == XTYPE_PASSWORD:
        d = self._x.get('generatedPassword', {})
        spec = {
            'length': d.get('length', 10),
            'include_symbols': d.get('includeSymbols', False),
            'base64': d.get('base64', True),
        }
        self._password = SchemaXPassword(**spec)
      elif xt == XTYPE_SERVICE_ACCOUNT:
        d = self._x.get('serviceAccount', {})
        self._service_account = SchemaXServiceAccount(d)
      elif xt == XTYPE_STORAGE_CLASS:
        d = self._x.get('storageClass', {})
        self._storage_class = SchemaXStorageClass(d)
      elif xt == XTYPE_STRING:
        d = self._x.get('string', {})
        self._string = SchemaXString(d)
      elif xt == XTYPE_REPORTING_SECRET:
        d = self._x.get('reportingSecret', {})
        self._reporting_secret = SchemaXReportingSecret(d)
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


class SchemaXImage:
  """Wrapper class providing convenient access to IMAGE and DEPLOYER_IMAGE properties."""

  def __init__(self, dictionary):
    self._split_by_colon = None
    self._split_to_registry_repo_tag = None

    generated_properties = dictionary.get('generatedProperties', {})
    if 'splitByColon' in generated_properties:
      s = generated_properties['splitByColon']
      if 'before' not in s:
        raise InvalidSchema(
            '"before" attribute is required within splitByColon')
      if 'after' not in s:
        raise InvalidSchema('"after" attribute is required within splitByColon')
      self._split_by_colon = (s['before'], s['after'])
    if 'splitToRegistryRepoTag' in generated_properties:
      s = generated_properties['splitToRegistryRepoTag']
      parts = ['registry', 'repo', 'tag']
      for name in parts:
        if name not in s:
          raise InvalidSchema(
              '"{}" attribute is required within splitToRegistryRepoTag'.format(
                  name))
      self._split_to_registry_repo_tag = tuple([s[name] for name in parts])

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
  """Wrapper class providing convenient access to SERVICE_ACCOUNT property."""

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
  """Wrapper class providing convenient access to STORAGE_CLASS property."""

  def __init__(self, dictionary):
    self._type = dictionary['type']

  @property
  def ssd(self):
    return self._type == 'SSD'


class SchemaXString:
  """Wrapper class providing convenient access to STRING property."""

  def __init__(self, dictionary):
    generated_properties = dictionary.get('generatedProperties', {})

    self._base64_encoded = generated_properties.get('base64Encoded', None)

  @property
  def base64_encoded(self):
    return self._base64_encoded


class SchemaXReportingSecret:
  """Wrapper class providing convenient access to REPORTING_SECRET property."""

  def __init__(self, dictionary):
    pass
