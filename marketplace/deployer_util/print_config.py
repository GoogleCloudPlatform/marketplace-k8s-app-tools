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

import re
import sys

from argparse import ArgumentParser

import yaml

import config_helper
import schema_values_common

_PROG_HELP = """
Outputs configuration parameters constructed from files in a directory.
The file names are parameter names, file contents parameter values.
The program supports several output formats, controlled by --output.
"""

_OUTPUT_HELP = """
Choose the format to output paremeter name-value pair.
shell: lines of VAR=VALUE, where the VALUEs are properly shell escaped.
yaml: a YAML file.
"""

OUTPUT_YAML = 'yaml'
OUTPUT_SHELL_VARS = 'shell_vars'

ENV_KEY_RE = re.compile(r'^[a-zA-z0-9_]+$')


class InvalidParameter(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument(
      '--output',
      '-o',
      help=_OUTPUT_HELP,
      choices=[OUTPUT_SHELL_VARS, OUTPUT_YAML],
      default=OUTPUT_YAML)
  parser.add_argument(
      '--xtype',
      help='If specified, outputs the values of the given x-google-marketplace'
      ' property.')
  parser.add_argument(
      '--key', help='If specified, outputs the keys, rather than the values')
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)

  try:
    if args.xtype:
      sys.stdout.write(output_xtype(values, schema, args.xtype, args.key))
      return

    if args.output == OUTPUT_SHELL_VARS:
      sys.stdout.write(output_shell_vars(values))
    elif args.output == OUTPUT_YAML:
      sys.stdout.write(output_yaml(values))
  finally:
    sys.stdout.flush()


def output_xtype(values, schema, xtype, print_keys):
  definition = {"x-google-marketplace": {"type": xtype}}
  candidates = schema.properties_matching(definition)
  if len(candidates) != 1:
    raise InvalidParameter(
        'There must be exactly one parameter matching but found {}: {}'.format(
            len(candidates), definition))
  key = candidates[0].name
  if print_keys:
    return key
  if key not in values:
    raise InvalidParameter('Parameter {} has no value'.format(key))
  return str(values[key])


def output_shell_vars(values):
  sorted_keys = list(values)
  sorted_keys.sort()
  invalid_keys = [key for key in sorted_keys if not ENV_KEY_RE.match(key)]
  if invalid_keys:
    raise config_helper.InvalidName(
        'Invalid config parameter names: {}'.format(invalid_keys))
  return ' '.join(['${}'.format(k) for k in sorted_keys])


def output_yaml(values):
  new_values = {}
  for key, value in values.items():
    current_new_values = new_values
    while '.' in key:
      key_prefix, key = key.split('.', 1)
      if key_prefix not in current_new_values:
        current_new_values[key_prefix] = {}
      current_new_values = current_new_values[key_prefix]
    current_new_values[key] = value

  return yaml.safe_dump(new_values, default_flow_style=False, indent=2)


if __name__ == "__main__":
  main()
