#!/usr/bin/env python3
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
import json
import os
from argparse import ArgumentParser

import yaml

import config_helper
import property_generator
import schema_values_common

_PROG_HELP = """
Modifies the configuration parameter files in a directory
according to their schema.
"""

_IMAGE_REPO_PREFIX_PROPERTY_NAME = '__image_repo_prefix__'


class InvalidProperty(Exception):
  pass


class MissingRequiredProperty(Exception):
  pass


class MissingRequiredValue(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument(
      '--final_values_file',
      help='Where the final value file should be written to',
      default='/data/final_values.yaml')
  parser.add_argument(
      '--app_uid',
      help='The application UID for populating into APPLICATION_UID properties',
      default='')
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  values = expand(values, schema, app_uid=args.app_uid)
  write_values(values, args.final_values_file)


def expand(values_dict, schema, app_uid=''):
  """Returns the expanded values according to schema."""
  schema.validate()

  valid_property_names = set(schema.properties.keys())
  valid_property_names.add(_IMAGE_REPO_PREFIX_PROPERTY_NAME)

  for k in values_dict:
    if k not in valid_property_names:
      raise InvalidProperty('No such property defined in schema: {}'.format(k))

  # Captures the final property name-value mappings.
  # This has both properties directly specified under schema's `properties` and
  # generated properties. See below for details about generated properties.
  result = {}
  # Captures only the generated properties. These are not directly specified in
  # the schema under `properties`. Rather, their name are specified in special
  # `generatedProperties` fields under each property's `x-google-marketplace`.
  # Note that properties with generated values are NOT generated properties.
  generated = {}

  if schema.is_v2():
    # Handles the images section of the schema.
    generate_v2_image_properties(schema, values_dict, generated)

  # Copy explicitly specified values and generate values into result.
  for k, prop in schema.properties.items():
    v = values_dict.get(k, None)

    # The value is not explicitly specified and
    # thus is eligible for auto-generation.
    if v is None:
      if prop.password:
        v = property_generator.generate_password(prop.password)
      elif prop.application_uid:
        v = app_uid or ''
      elif prop.tls_certificate:
        v = property_generator.generate_tls_certificate()
      elif prop.xtype == config_helper.XTYPE_ISTIO_ENABLED:
        # For backward compatibility.
        v = False
      elif prop.xtype == config_helper.XTYPE_INGRESS_AVAILABLE:
        # For backward compatibility.
        v = True
      elif prop.xtype == config_helper.XTYPE_DEPLOYER_IMAGE:
        v = maybe_derive_deployer_image(schema, values_dict)
      elif prop.default is not None:
        v = prop.default

    # Generate additional properties from this property.
    if v is not None:
      if prop.image:
        if not isinstance(v, str):
          raise InvalidProperty(
              'Invalid value for IMAGE property {}: {}'.format(k, v))
        generate_v1_properties_for_image(prop, v, generated)
      elif prop.string:
        if not isinstance(v, str):
          raise InvalidProperty(
              'Invalid value for STRING property {}: {}'.format(k, v))
        generate_properties_for_string(prop, v, generated)
      elif prop.tls_certificate:
        if not isinstance(v, str):
          raise InvalidProperty(
              'Invalid value for TLS_CERTIFICATE property {}: {}'.format(k, v))
        generate_properties_for_tls_certificate(prop, v, generated)
      elif prop.application_uid:
        generate_properties_for_appuid(prop, v, generated)

    if v is not None:
      result[k] = v

  validate_value_types(result, schema)
  validate_required_props(result, schema)

  # Copy generated properties into result, validating no collisions.
  for k, v in generated.items():
    if k in result:
      raise InvalidProperty(
          'The property is to be generated, but already has a value: {}'.format(
              k))
    result[k] = v
  return result


def validate_required_props(values, schema):
  for k in schema.required:
    if k not in values:
      raise MissingRequiredProperty(
          'No value for required property: {}'.format(k))


def validate_value_types(values, schema):
  for k, v in values.items():
    prop = schema.properties[k]
    if not isinstance(v, prop.type):
      raise InvalidProperty(
          'Property {} is expected to be of type {}, but has value: {}'.format(
              k, prop.type, v))


def maybe_derive_deployer_image(schema, values_dict):
  if not schema.is_v2():
    return None
  repo_prefix = values_dict.get(_IMAGE_REPO_PREFIX_PROPERTY_NAME, None)
  if not repo_prefix:
    raise MissingRequiredValue('A valid value for __image_repo_prefix__ '
                               'must be specified in values.yaml')
  tag = schema.x_google_marketplace.published_version
  return '{}/{}:{}'.format(repo_prefix, 'deployer', tag)


def generate_properties_for_appuid(prop, value, result):
  if prop.application_uid.application_create:
    result[prop.application_uid.application_create] = False if value else True


def generate_v1_properties_for_image(prop, value, result):
  if prop.image.split_by_colon:
    before_name, after_name = prop.image.split_by_colon
    parts = value.split(':', 1)
    if len(parts) != 2:
      raise InvalidProperty(
          'Property {} has value that does not contain a colon: {}'.format(
              prop.name, value))
    before_value, after_value = parts
    result[before_name] = before_value
    result[after_name] = after_value
  if prop.image.split_to_registry_repo_tag:
    reg_name, repo_name, tag_name = prop.image.split_to_registry_repo_tag
    parts = value.split(':', 1)
    if len(parts) != 2:
      raise InvalidProperty(
          'Property {} has value that does not contain a tag: {}'.format(
              prop.name, value))
    nontag_value, tag_value = parts
    parts = nontag_value.split('/', 1)
    if len(parts) != 2:
      raise InvalidProperty(
          'Property {} has value that does not include a registry: {}'.format(
              prop.name, value))
    reg_value, repo_value = parts
    result[reg_name] = reg_value
    result[repo_name] = repo_value
    result[tag_name] = tag_value


def generate_v2_image_properties(schema, values_dict, result):
  repo_prefix = values_dict.get(_IMAGE_REPO_PREFIX_PROPERTY_NAME, None)
  if not repo_prefix:
    raise MissingRequiredValue('A valid value for __image_repo_prefix__ '
                               'must be specified in values.yaml')
  tag = schema.x_google_marketplace.published_version
  for img in schema.x_google_marketplace.images.values():
    if img.name:
      # Allows an empty image name for legacy reason.
      registry_repo = '{}/{}'.format(repo_prefix, img.name)
    else:
      registry_repo = repo_prefix
    registry, repo = registry_repo.split('/', 1)
    full = '{}:{}'.format(registry_repo, tag)
    for prop in img.properties.values():
      if prop.part_type == config_helper.IMAGE_PROJECTION_TYPE_FULL:
        result[prop.name] = full
      elif prop.part_type == config_helper.IMAGE_PROJECTION_TYPE_REGISTRY:
        result[prop.name] = registry
      elif prop.part_type == config_helper.IMAGE_PROJECTION_TYPE_REGISTRY_REPO:
        result[prop.name] = registry_repo
      elif prop.part_type == config_helper.IMAGE_PROJECTION_TYPE_REPO:
        result[prop.name] = repo
      elif prop.part_type == config_helper.IMAGE_PROJECTION_TYPE_TAG:
        result[prop.name] = tag
      else:
        raise InvalidProperty(
            'Invalid type for images.properties.type: {}'.format(
                prop.part_type))


def generate_properties_for_string(prop, value, result):
  if prop.string.base64_encoded:
    result[prop.string.base64_encoded] = base64.b64encode(value.encode('ascii'))


def generate_properties_for_tls_certificate(prop, value, result):
  certificate = json.loads(value)
  if prop.tls_certificate.base64_encoded_private_key:
    result[prop.tls_certificate.base64_encoded_private_key] = base64.b64encode(
        certificate['private_key'].encode('ascii')).decode('ascii')
  if prop.tls_certificate.base64_encoded_certificate:
    result[prop.tls_certificate.base64_encoded_certificate] = base64.b64encode(
        certificate['certificate'].encode('ascii')).decode('ascii')


def write_values(values, values_file):
  if not os.path.exists(os.path.dirname(values_file)):
    os.makedirs(os.path.dirname(values_file))
  with open(values_file, 'w', encoding='utf-8') as f:
    data = yaml.safe_dump(values, default_flow_style=False, indent=2)
    f.write(data)


if __name__ == "__main__":
  main()
