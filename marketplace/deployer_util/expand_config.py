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
import config_helper
import os

_PROG_HELP = """
Modifies the configuration parameter files in a directory
according to their schema.
"""

CODEC_UTF8 = 'utf_8'
CODEC_ASCII = 'ascii'


class InvalidProperty(Exception):
  pass


class MissingRequiredProperty(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--values_dir',
                      help='Where the value files should be read from',
                      default='/data/values')
  parser.add_argument('--final_values_dir',
                      help='Where the final value files should be written to',
                      default='/data/final_values')
  parser.add_argument('--schema_file', help='Path to the schema file',
                      default='/data/schema.yaml')
  parser.add_argument('--schema_file_encoding',
                      help='Encoding of the schema file',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  parser.add_argument('--encoding',
                      help='Encoding of the value files',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  args = parser.parse_args()

  schema = config_helper.Schema.load_yaml_file(args.schema_file,
                                               args.schema_file_encoding)
  values = config_helper.read_values_to_dict(args.values_dir, args.encoding)
  values = expand(values, schema)
  write_values(values, args.final_values_dir, args.encoding)


def expand(values_dict, schema):
  """Returns the expanded values according to schema."""
  for k in values_dict:
    if k not in schema.properties:
      raise InvalidProperty('No such property defined in schema: {}'.format(k))

  result = {}
  for k, prop in schema.properties.iteritems():
    v = values_dict.get(k, None)

    if v is None and prop.password:
      result[k] = generate_password(prop.password)
      continue

    if v is None and prop.default is not None:
      v = prop.default

    if v is not None:
      result[k] = v

  validate_required_props(result, schema)
  return result


def validate_required_props(values, schema):
  for k in schema.required:
    if k not in values:
      raise MissingRequiredProperty(
          'No value for required property: {}'.format(k))


def generate_password(config):
  pw = GeneratePassword(config.length, config.include_symbols)
  if config.base64:
    pw = base64.b64encode(pw)
  return pw


def write_values(values, values_dir, encoding):
  if not os.path.exists(values_dir):
    os.makedirs(values_dir)
  for k, v in values.iteritems():
    file_path = os.path.join(values_dir, k)
    with open(file_path, 'w') as f:
      f.write(v.encode(encoding))


if __name__ == "__main__":
  main()
