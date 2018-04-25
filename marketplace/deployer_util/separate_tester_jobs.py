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

''' Separate the tester job from resources manifest into a different manifest'''

parser = ArgumentParser()

parser.add_argument("-m", "--manifest", dest="manifest",
                    help="the configuration for tests")
parser.add_argument("-tc", "--test_config", dest="test_config",
                    help="the configuration for tests")
parser.add_argument("-tm", "--tester_manifest", dest="tester_manifest",
                    help="the output for test resources")

args = parser.parse_args()

resources = load_resources_yaml(args.manifest)

test_config = load_yaml(args.test_config)
  
temp_resources = args.manifest + ".tmp"
with open(temp_resources, "w") as outfile:
  for resource in resources:
    outfile.write(docstart)

    is_test_resource = False
    if test_config and test_config['jobname']:
      if resource['kind'] == "Job" and resource['metadata']['name'] == test_config['jobname']:
        is_test_resource = True

    if is_test_resource:
      with open(args.tester_manifest, "w") as test_outfile:
        yaml.dump(resource, test_outfile, default_flow_style=False)
    else:
      yaml.dump(resource, outfile, default_flow_style=False)

os.rename(temp_resources, args.manifest)