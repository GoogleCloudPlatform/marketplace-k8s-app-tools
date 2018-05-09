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

import yaml

NAME_RE = re.compile(r'[a-zA-z0-9_]+$')

XGOOGLE = 'x-google-marketplace'
XTYPE_PASSWORD = 'GENERATED_PASSWORD'


class InvalidName(Exception):
  pass


class InvalidSchema(Exception):
  pass


def read_values_to_dict(values_dir, codec, schema):
  """Returns a dict constructed from files in values_dir."""
  files = [f for f in os.listdir(values_dir)
           if os.path.isfile(os.path.join(values_dir, f))]
  result = {}
  for filename in files:
    if not NAME_RE.match(filename):
      raise InvalidName('Invalid config parameter name: {}'.format(filename))
    file_path = os.path.join(values_dir, filename)
    with open(file_path, "r") as f:
      data = f.read().decode(codec)
      result[filename] = data

  # Data read in as strings. Convert them to proper types defined in schema.
  result = {k: schema.properties[k].str_to_type(v) if k in schema.properties
            else v
            for k, v in result.iteritems()}
  return result


class Schema:
  """Wrapper class providing convenient access to a JSON schema."""

  @staticmethod
  def load_yaml_file(filepath, encoding='utf_8'):
    with io.open(filepath, 'r', encoding=encoding) as f:
      d = yaml.load(f)
      return Schema(d)

  @staticmethod
  def load_yaml(yaml_str):
    return Schema(yaml.load(yaml_str))

  def __init__(self, dictionary):
    self._required = dictionary.get('required', [])
    self._properties = {
        k: SchemaProperty(k, v)
        for k, v in dictionary.get('properties', {}).iteritems()
    }

  @property
  def required(self):
    return self._required

  @property
  def properties(self):
    return self._properties


class SchemaProperty:
  """Wrapper class providing convenient access to a JSON schema property."""

  def __init__(self, name, dictionary):
    self._name = name
    self._d = dictionary
    self._default = dictionary.get('default', None)
    self._x = dictionary.get(XGOOGLE, None)
    self._password = None

    if 'type' not in dictionary:
      raise InvalidSchema('Property {} has no type'.format(name))
    self._type = {'int': int,
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
        raise InvalidSchema('Property {} has a default value of invalid type'.
                            format(name))

    if self._x:
      if 'type' not in self._x:
        raise InvalidSchema(
            'Property {} has {} without a type'.format(name, XGOOGLE))
      xt = self._x['type']
      if xt == XTYPE_PASSWORD:
        d = self._x.get('generatedPassword', {})
        spec = {
            'length': d.get('length', 10),
            'include_symbols': d.get('includeSymbols', False),
            'base64': d.get('base64', True),
        }
        self._password = SchemaXPassword(**spec)

  @property
  def name(self):
    return self._name

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
  def password(self):
    return self._password

  def str_to_type(self, str_val):
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
        dict(list(self._d.iteritems()) + [('name', self._name)]),
        definition)

  def __eq__(self, other):
    if not isinstance(other, SchemaProperty):
      return False
    return other._name == self._name and other._d == self._d


SchemaXPassword = collections.namedtuple('SchemaXPassword',
                                         ['length',
                                          'include_symbols',
                                          'base64'])
