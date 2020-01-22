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

import os

from yaml_util import overlay_yaml_file
from argparse import ArgumentParser
''' Copy all the files from the test manifest into final manifest.
    The values.yaml file is merged instead of overwriten '''

parser = ArgumentParser()

parser.add_argument(
    "-tc", "--manifest", dest="manifest", help="the configuration for tests")
parser.add_argument(
    "-td",
    "--test_manifest",
    dest="test_manifest",
    help="the output for test resources")

args = parser.parse_args()

for parent, dir_list, file_list in os.walk(args.test_manifest):
  for filename in file_list:
    orig = os.path.join(parent, filename)
    dest = parent[len(args.test_manifest) + 1:]
    dest = os.path.join(args.manifest, dest)
    if not os.path.exists(dest):
      os.makedirs(dest)
    dest = os.path.join(dest, filename)
    if filename == "values.yaml":
      overlay_yaml_file(orig, dest)
    else:
      os.rename(orig, dest)
