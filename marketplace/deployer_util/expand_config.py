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

from argparse import ArgumentParser
from password import GeneratePassword
import base64
import os
import re
import yaml


_PROG_HELP = """
Modifies the configuration parameter files in a directory
according to their schema.
"""

CODEC_UTF8 = 'UTF-8'
CODEC_ASCII = 'ASCII'

XGOOGLE = 'x-googleMarketplace'
XTYPE_PASSWORD = 'GENERATED_PASSWORD'
XTYPE_PASSWORD_KEY = 'generatedPassword'

NAME_RE=re.compile(r'[a-zA-z0-9_]+$')


class InvalidProperty(Exception):
  pass


class MissingRequiredProperty(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--values_dir',
                      help='Where the value files should be read from '
                      'and written back to',
                      default='/data/values')
  parser.add_argument('--schema_file', help='Path to the schema file',
                      default='/data/schema.yaml')
  parser.add_argument('--encoding',
                      help='Encoding of the value files',
                      choices=[CODEC_UTF8, CODEC_ASCII], default='UTF-8')
  args = parser.parse_args()

  schema = read_schema(args.schema_file)
  values = read_values_to_dict(args.values_dir, args.encoding)
  values = expand(values, schema)
  write_values(values, args.values_dir, args.encoding)


def read_values_to_dict(values_dir, codec):
  """Returns a dict construted from files in values_dir."""
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
  return result


def read_schema(schema_file):
  """Returns a nest dictionary for the JSON schema content."""
  with open(schema_file, "r") as f:
    return yaml.load(f)


def expand(values, schema):
  """Returns the expanded values according to schema."""
  props = schema.get('properties', {})
  all_keys = (list(values) + list(props))
  result = {}
  for k in all_keys:
    if k not in props:
      raise InvalidProperty('No such property defined in schema: {}'.format(k))
    prop = props[k]
    v = values.get(k, None)

    xgoogle = prop.get(XGOOGLE, {})
    xtype = xgoogle.get('type', None)
    if v is None and xtype == XTYPE_PASSWORD:
      password_config = xgoogle.get(XTYPE_PASSWORD_KEY, {})
      result[k] = generate_password(password_config)
      continue

    if v is None and 'default' in prop:
      v = prop['default']

    if v is not None:
      result[k] = v

  validate_required_props(result, schema)
  return result


def validate_required_props(values, schema):
  requireds = schema.get('required', [])
  for k in requireds:
    if k not in values:
      raise MissingRequiredProperty(
          'No value for required property: {}'.format(k))


def generate_password(config):
  length = config.get('length', 10)
  include_symbols = config.get('includeSymbols', False)
  use_base64 = config.get('base64', True)
  pw = GeneratePassword(length, include_symbols)
  if use_base64:
    pw = base64.b64encode(pw)
  return pw


def write_values(values, values_dir, encoding):
  for k, v in values.iteritems():
    file_path = os.path.join(values_dir, k)
    with open(file_path, 'w') as f:
      f.write(v.encode(encoding))


if __name__ == "__main__":
  main()
