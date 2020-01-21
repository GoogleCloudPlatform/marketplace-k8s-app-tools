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

import yaml
import os.path
from argparse import ArgumentParser

import log_util as log
from constants import LOG_SMOKE_TEST
from dict_util import deep_get
from yaml_util import load_yaml

_PROG_HELP = """
Overlay properties declared in the test schema over the original
schema, dumping the content into a specified target.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--test_schema', help='Test schema file', required=True)
  parser.add_argument(
      '--original_schema', help='Original schema file', required=True)
  parser.add_argument(
      '--output',
      action='append',
      default=[],
      help='Location(s) of the file(s) to output the overlayed schema')
  args = parser.parse_args()

  if os.path.isfile(args.test_schema):
    test_schema = load_yaml(args.test_schema)
  else:
    log.info(
        '{} Test schema file {} does not exist. '
        'Using the original schema.', LOG_SMOKE_TEST, args.test_schema)
    test_schema = {}

  output_schema = load_yaml(args.original_schema)
  output_schema['properties'] = output_schema.get('properties', {})
  for prop in test_schema.get('properties', {}):
    test_type = deep_get(test_schema, 'properties', prop,
                         'x-google-marketplace', 'type')
    output_type = deep_get(output_schema, 'properties', prop,
                           'x-google-marketplace', 'type')
    if (test_type != output_type):
      raise Exception(
          'Changing x-google-marketplace type is not allowed. Property: {}',
          prop)
    output_schema['properties'][prop] = test_schema['properties'][prop]

  for output in args.output:
    with open(output, 'w', encoding='utf-8') as f:
      yaml.dump(output_schema, f)


if __name__ == "__main__":
  main()
