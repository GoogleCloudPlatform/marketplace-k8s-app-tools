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
import yaml

from yaml_util import load_resources_yaml
from argparse import ArgumentParser
'''Scans a manifest for an Application resource and sets the assembly phase.'''

parser = ArgumentParser()

parser.add_argument(
    "-m", "--manifest", dest="manifest", help="the manifest file")
parser.add_argument(
    "-s",
    "--status",
    dest="status",
    choices=['Failure', 'Pending', 'Success'],
    help="the assembly status to set")

args = parser.parse_args()

assert args.manifest
assert os.path.exists(args.manifest)

resources = []
for r in load_resources_yaml(args.manifest):
  resources.append(r)
apps = [r for r in resources if r['kind'] == "Application"]

if len(apps) == 0:
  raise Exception(
      "Set of resources in {:s} does not include one of "
      "Application kind. See {:s} for how to add to a "
      "helm-based deployer. See {:s} for an envsubst example.".format(
          args.manifest,
          "https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer-helm.md",
          "https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer-envsubst.md"
      ))
if len(apps) > 1:
  raise Exception("Set of resources in {:s} includes more than one of "
                  "Application kind".format(args.manifest))

apps[0]['spec']['assemblyPhase'] = args.status

with open(args.manifest, "w", encoding='utf-8') as outfile:
  yaml.safe_dump_all(resources, outfile, default_flow_style=False, indent=2)
