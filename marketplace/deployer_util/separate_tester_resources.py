#!/usr/bin/env python
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
import yaml

from argparse import ArgumentParser
from constants import GOOGLE_CLOUD_TEST
from dict_util import deep_get
from resources import set_resource_ownership
from yaml_util import load_resources_yaml
from yaml_util import load_yaml

_PROG_HELP = "Separate the tester job from resources manifest into a different manifest"

def main():

  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument("--appname", help="the name of the applictation instance")
  parser.add_argument("--appuid", help="the uid of the applictation instance")
  parser.add_argument("--manifest", help="the configuration for tests")
  parser.add_argument("--tester_manifest", help="the output for test resources")
  args = parser.parse_args()

  resources = load_resources_yaml(args.manifest)

  test_resources = []
  nontest_resources = []
  for resource in resources:
    full_name = "{}/{}".format(resource['kind'], deep_get(resource, 'metadata', 'name'))
    if deep_get(resource, 'metadata', 'annotations', GOOGLE_CLOUD_TEST) == 'test':
      print("INFO Tester resource: {}".format(full_name))
      set_resource_ownership(args.appuid, args.appname, resource)
      test_resources.append(resource)
    else:
      print("INFO Prod resource: {}".format(full_name))
      nontest_resources.append(resource)

  temp_manifest = args.manifest + ".tmp"
  if nontest_resources:
    with open(temp_manifest, "w") as outfile:
      yaml.safe_dump_all(nontest_resources, outfile, default_flow_style=False)
  os.rename(temp_manifest, args.manifest)

  if test_resources:
    with open(args.tester_manifest, "a") as test_outfile:
      yaml.safe_dump_all(test_resources, test_outfile, default_flow_style=False)


if __name__ == "__main__":
  main()
