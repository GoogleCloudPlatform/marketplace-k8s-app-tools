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

import base64
import os
from argparse import ArgumentParser

import yaml

import schema_values_common
from password import GeneratePassword

_PROG_HELP = """
Modifies the configuration parameter files in a directory
according to their schema.
"""


class InvalidProperty(Exception):
  pass


class MissingRequiredProperty(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(
      parser, values_file='/data/values.yaml', values_dir='/data/values')
  parser.add_argument(
      '--final_values_file',
      help='Where the final value file should be written to',
      default='/data/final_values.yaml')
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  values = expand(values, schema)
  write_values(values, args.final_values_file)


def expand(values_dict, schema):
  """Returns the expanded values according to schema."""
  schema.validate()

  for k in values_dict:
    if k not in schema.properties:
      raise InvalidProperty('No such property defined in schema: {}'.format(k))

  result = {}
  generated = {}
  for k, prop in schema.properties.iteritems():
    v = values_dict.get(k, None)

    if v is None and prop.password:
      if prop.type != str:
        raise InvalidProperty(
            'Property {} is expected to be of type string'.format(k))
      result[k] = generate_password(prop.password)
      continue

    if v is None and prop.default is not None:
      v = prop.default

    if v is not None and prop.image:
      if not isinstance(v, str):
        raise InvalidProperty('Invalid value for IMAGE property {}: {}'.format(
            k, v))
      generate_properties_for_image(prop, v, generated)

    # TODO: Handle CERTIFICATE properties.
    #
    # Strawman Approach:
    #
    # CERTIFICATE property is expected to have a json value of the following form:
    # {
    #   "key": "...",
    #   "crt": "..."
    # }
    # 
    # If not specified, generate a CERTIFICATE property value via openssl.
    #
    # Generate a property with key equal to certificate.base64EncodedKey
    # and value equal to the "key" field of the json contained in
    # CERTIFICATE property.
    #
    # Generate a property with crt equal to certificate.base64EncodedCrt
    # and value equal to the "crt" field of the json contained in
    # CERTIFICATE property.

    if v is not None and prop.string:
      if not isinstance(v, str):
        raise InvalidProperty('Invalid value for STRING property {}: {}'.format(
            k, v))
      generate_properties_for_string(prop, v, generated)

    if v is not None:
      result[k] = v

  validate_value_types(result, schema)
  validate_required_props(result, schema)

  for k, v in generated.iteritems():
    if k in result:
      raise InvalidProperty(
          'The property is to be generated, but already has a value: {}'
          .format(k))
    result[k] = v
  return result


def validate_required_props(values, schema):
  for k in schema.required:
    if k not in values:
      raise MissingRequiredProperty(
          'No value for required property: {}'.format(k))


def validate_value_types(values, schema):
  for k, v in values.iteritems():
    prop = schema.properties[k]
    if not isinstance(v, prop.type):
      raise InvalidProperty(
          'Property {} is expected to be of type {}, but has value: {}'.format(
              k, prop.type, v))


def generate_properties_for_image(prop, value, result):
  if prop.image.split_by_colon:
    before_name, after_name = prop.image.split_by_colon
    parts = value.split(':', 1)
    if len(parts) != 2:
      raise InvalidProperty(
          'Property {} has a value that does not contain a colon'.format(
              prop.name, value))
    before_value, after_value = parts
    result[before_name] = before_value
    result[after_name] = after_value


def generate_properties_for_string(prop, value, result):
  if prop.string.base64_encoded:
    result[prop.string.base64_encoded] = base64.b64encode(value)


def generate_password(config):
  pw = GeneratePassword(config.length, config.include_symbols)
  if config.base64:
    pw = base64.b64encode(pw)
  return pw


def write_values(values, values_file):
  if not os.path.exists(os.path.dirname(values_file)):
    os.makedirs(os.path.dirname(values_file))
  with open(values_file, 'w') as f:
    data = yaml.safe_dump(values, default_flow_style=False, indent=2)
    f.write(data)


if __name__ == "__main__":
  main()
