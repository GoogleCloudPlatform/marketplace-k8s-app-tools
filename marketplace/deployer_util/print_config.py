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
import json
import sys
import yaml

from argparse import ArgumentParser


import config_helper

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
CODEC_UTF8 = 'utf_8'
CODEC_ASCII = 'ascii'


class InvalidParameter(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--output', '-o', help=_OUTPUT_HELP,
                      choices=[OUTPUT_SHELL_VARS, OUTPUT_YAML],
                      default=OUTPUT_YAML)
  parser.add_argument('--values_dir', help='Where to read value files',
                      default='/data/final_values')
  parser.add_argument('--schema_file', help='Path to the schema file',
                      default='/data/schema.yaml')
  parser.add_argument('--schema_file_encoding',
                      help='Encoding of the schema file',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  parser.add_argument('--param',
                      help='If specified, outputs the value of a single '
                      'parameter unescaped. The value here is a JSON '
                      'which should partially match the parameter schema.')
  parser.add_argument('--decoding',
                      help='Codec used for decoding value file contents',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  parser.add_argument('--encoding',
                      help='Codec for encoding output files',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  args = parser.parse_args()

  schema = config_helper.Schema.load_yaml_file(args.schema_file,
                                               args.schema_file_encoding)
  values = config_helper.read_values_to_dict(args.values_dir,
                                             args.decoding,
                                             schema)

  try:
    if args.param:
      definition = json.loads(args.param)
      sys.stdout.write(output_param(values, schema, definition))
      return

    if args.output == OUTPUT_SHELL_VARS:
      sys.stdout.write(output_shell_vars(values))
    elif args.output == OUTPUT_YAML:
      sys.stdout.write(output_yaml(values, args.encoding))
  finally:
    sys.stdout.flush()


def output_param(values, schema, definition):
  candidates = [k for k, v in schema.properties.iteritems()
                if v.matches_definition(definition)]
  if len(candidates) != 1:
    raise InvalidParameter(
        'There must be exactly one parameter matching but found {}: {}'
        .format(len(candidates), definition))
  key = candidates[0]
  if key not in values:
    raise InvalidParameter('Parameter {} has no value'.format(key))
  return str(values[key])


def output_shell_vars(values):
  sorted_keys = list(values)
  sorted_keys.sort()
  return ' '.join(['${}'.format(k) for k in sorted_keys])


def output_yaml(values, encoding):
  new_values = {}
  for key, value in values.items():
    current_new_values = new_values
    while '.' in key:
      key_prefix, key = key.split('.', 1)
      if key_prefix not in current_new_values:
        current_new_values[key_prefix] = {}

      current_new_values = current_new_values[key_prefix]
    current_new_values[key] = value

  return yaml.safe_dump(new_values,
                        encoding=encoding,
                        default_flow_style=False,
                        indent=2)



if __name__ == "__main__":
  main()
