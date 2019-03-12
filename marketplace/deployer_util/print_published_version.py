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

import sys

from argparse import ArgumentParser

import schema_values_common

_PROG_HELP = """
Print the published version declared in the schema.
Requires schema.yaml version v2.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  schema.validate()
  if (schema.x_google_marketplace is None or
      not schema.x_google_marketplace.is_v2()):
    raise Exception('schema.yaml must be in v2 version')

  sys.stdout.write(schema.x_google_marketplace.published_version)
  sys.stdout.flush()


if __name__ == "__main__":
  main()
