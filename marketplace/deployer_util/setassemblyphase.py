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

import os
import yaml

from yaml_util import load_resources_yaml
from yaml_util import docstart
from argparse import ArgumentParser

'''Scans a manifest for an Application resource and sets the assembly phase.'''

parser = ArgumentParser()

parser.add_argument("-m", "--manifest", dest="manifest",
                    help="the manifest file")
parser.add_argument("-s", "--status", dest="status",
                    help="the assembly status to set")

args = parser.parse_args()

assert args.status
assert args.status in ['Failure', 'Pending', 'Success']
assert args.manifest
assert os.path.exists(args.manifest)

resources = []
for r in load_resources_yaml(args.manifest):
  resources.append(r)
apps = [ r for r in resources if r['kind'] == "Application" ]

if len(apps) == 0:
  raise Exception("Set of resources in {:s} does not include one of Application kind")
if len(apps) > 1:
  raise Exception("Set of resources in {:s} includes more than one of Application kind")

apps[0]['spec']['assemblyPhase'] = args.status

with open(args.manifest, "w") as outfile:
  for resource in resources:
    outfile.write(docstart)
    yaml.dump(resource, outfile, default_flow_style=False)
