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

import sys

from argparse import ArgumentParser

import config_helper

_PROG_HELP = """
Parses the provided schema file and prints all x-google-marketplace
properties that match the provided type.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument(
      '--schema_file',
      help='Path to the schema file',
      default='/data/schema.yaml')
  parser.add_argument(
      '--type',
      help='The x-google-marketplace type for which '
      'configuration keys will be printed.\n'
      'Example: NAME',
      required=True)
  args = parser.parse_args()

  schema = config_helper.Schema.load_yaml_file(args.schema_file)
  sys.stdout.write('\n'.join(
      [k for k, v in schema.properties.items() if v.xtype == args.type]))


if __name__ == "__main__":
  main()
