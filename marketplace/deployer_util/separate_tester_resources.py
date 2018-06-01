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

from yaml_util import load_resources_yaml
from yaml_util import load_yaml
from yaml_util import docstart
from argparse import ArgumentParser
from dict_util import DictWalker

_PROG_HELP = "Separate the tester job from resources manifest into a different manifest"

def main():
  _GOOGLE_CLOUD_TEST = 'marketplace.cloud.google.com/verification'

  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument("--manifest", help="the configuration for tests")
  parser.add_argument("--tester_manifest", help="the output for test resources")
  args = parser.parse_args()

  resources = load_resources_yaml(args.manifest)

  temp_resources = args.manifest + ".tmp"
  with open(temp_resources, "w") as outfile:
    for resource in resources:
      resource = DictWalker(resource)
      outfile.write(docstart)

      full_name = "{}/{}".format(resource['kind'], resource[['metadata', 'name']])
      if resource[['metadata', 'annotations', _GOOGLE_CLOUD_TEST]] == 'test':
        with open(args.tester_manifest, "a") as test_outfile:
          print("INFO Tester resource: {}".format(full_name))
          test_outfile.write(docstart)
          yaml.dump(resource.dict, test_outfile, default_flow_style=False)
      else:
        print("INFO Prod resource: {}".format(full_name))
        yaml.dump(resource.dict, outfile, default_flow_style=False)

  os.rename(temp_resources, args.manifest)


if __name__ == "__main__":
  main()
