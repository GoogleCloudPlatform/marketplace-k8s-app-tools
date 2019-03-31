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
import json
import os
import OpenSSL
from argparse import ArgumentParser

import yaml

import config_helper
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

  for k in values_dict:
    if k not in schema.properties:
      raise InvalidProperty('No such property defined in schema: {}'.format(k))

  result = {}
  generated = {}
  for k, prop in schema.properties.iteritems():
    v = values_dict.get(k, None)

    # The value is not delivered to the framework, so it can be filled by the framework.
    # For example, a password is generated.
    if v is None:
      if prop.password:
        v = generate_password(prop.password)
      elif prop.application_uid:
        v = app_uid or ''
        generate_properties_for_appuid(prop, app_uid, generated)
      elif prop.certificate:
        v = generate_certificate()
      elif prop.xtype == config_helper.XTYPE_ISTIO_ENABLED:
        # For backward compatibility.
        v = False
      elif prop.xtype == config_helper.XTYPE_INGRESS_AVAILABLE:
        # For backward compatibility.
        v = True
      elif prop.default is not None:
        v = prop.default

    # The value is not empty, so it can be expanded to the special properties.
    # For example, property IMAGE can be expanded from the raw string image,
    # to the generatedProperties properties.
    if v is not None:
      if prop.image:
        if not isinstance(v, str):
          raise InvalidProperty(
              'Invalid value for IMAGE property {}: {}'.format(k, v))
        generate_properties_for_image(prop, v, generated)
      elif prop.string:
        if not isinstance(v, str):
          raise InvalidProperty(
              'Invalid value for STRING property {}: {}'.format(k, v))
        generate_properties_for_string(prop, v, generated)
      elif prop.certificate:
        if not isinstance(v, str):
          raise InvalidProperty(
              'Invalid value for CERTIFICATE property {}: {}'.format(k, v))
        generate_properties_for_certificate(prop, v, generated)

    # At this point, the property is populated and expanded, so overwrite the returned value.
    if v is not None:
      result[k] = v

  validate_value_types(result, schema)
  validate_required_props(result, schema)

  for k, v in generated.iteritems():
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
  for k, v in values.iteritems():
    prop = schema.properties[k]
    if not isinstance(v, prop.type):
      raise InvalidProperty(
          'Property {} is expected to be of type {}, but has value: {}'.format(
              k, prop.type, v))


def generate_properties_for_appuid(prop, value, result):
  if prop.application_uid.application_create:
    result[prop.application_uid.application_create] = False if value else True


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
  if prop.image._split_to_registry_repo_tag:
    reg_name, repo_name, tag_name = prop.image._split_to_registry_repo_tag
    parts = value.split(':', 1)
    if len(parts) != 2:
      raise InvalidProperty(
          'Property {} has a value that does not contain a tag'.format(
              prop.name, value))
    nontag_value, tag_value = parts
    parts = nontag_value.split('/', 1)
    if len(parts) != 2:
      raise InvalidProperty(
          'Property {} has a value that does not include a registry'.format(
              prop.name, value))
    reg_value, repo_value = parts
    result[reg_name] = reg_value
    result[repo_name] = repo_value
    result[tag_name] = tag_value


def generate_properties_for_string(prop, value, result):
  if prop.string.base64_encoded:
    result[prop.string.base64_encoded] = base64.b64encode(value)


def generate_password(config):
  pw = GeneratePassword(config.length, config.include_symbols)
  if config.base64:
    pw = base64.b64encode(pw)
  return pw


def generate_certificate():
  cert_seconds_to_expiry = 60 * 60 * 24 * 365  # one year

  key = OpenSSL.crypto.PKey()
  key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

  crt = OpenSSL.crypto.X509()
  crt.get_subject().C = 'US'
  crt.get_subject().OU = 'Temporary Certificate'
  crt.get_subject().CN = 'Temporary Certificate'
  crt.gmtime_adj_notBefore(0)
  crt.gmtime_adj_notAfter(cert_seconds_to_expiry)
  crt.set_issuer(crt.get_subject())
  crt.set_pubkey(key)
  crt.sign(key, 'sha1')

  return json.dumps({
      'key': OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key),
      'crt': OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, crt)
  })


def generate_properties_for_certificate(prop, value, result):
  certificate = json.loads(value)
  if prop.certificate.base64_encoded_key:
    result[prop.certificate.base64_encoded_key] = base64.b64encode(
        certificate['key'])
  if prop.certificate.base64_encoded_crt:
    result[prop.certificate.base64_encoded_crt] = base64.b64encode(
        certificate['crt'])


def write_values(values, values_file):
  if not os.path.exists(os.path.dirname(values_file)):
    os.makedirs(os.path.dirname(values_file))
  with open(values_file, 'w') as f:
    data = yaml.safe_dump(values, default_flow_style=False, indent=2)
    f.write(data)


if __name__ == "__main__":
  main()
