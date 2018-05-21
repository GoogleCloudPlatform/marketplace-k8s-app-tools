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
import json

from argparse import ArgumentParser

import config_helper


_PROG_HELP = """
Parses the provided schema file and prints all x-google-marketplace
properties that match the provided type.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--values',
                      help='Values json.\n'
                           'Example: { "foo": "bar" }',
                      required=True)
  parser.add_argument('--key',
                      help='The value to be extracted.\n'
                           'Example: foo',
                      required=True)
  args = parser.parse_args()

  sys.stdout.write(json.loads(args.values)[args.key])


if __name__ == "__main__":
  main()
