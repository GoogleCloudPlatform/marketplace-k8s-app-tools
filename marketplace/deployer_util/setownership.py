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
from yaml_util import docstart
from argparse import ArgumentParser

''' Scans the manifest folder kubernetes resources and set the Application to own
    the ones defined in its list of components kinds '''

parser = ArgumentParser()

parser.add_argument("-n", "--appname", dest="appname",
                    help="the name of the applictation instante")
parser.add_argument("-i", "--appuid", dest="appuid",
                    help="the uid of the applictation instante")
parser.add_argument("-m", "--manifests", dest="manifests",
                    help="the folder containing the manifest templates")
parser.add_argument("-d", "--dest", dest="dest",
                    help="the output file for the resulting manifest")

args = parser.parse_args()

resources = []
for filename in os.listdir(args.manifests):
  docs = load_resources_yaml(os.path.join(args.manifests, filename))
  map(lambda doc: resources.append(doc), docs)

apps = [ r for r in resources if r['kind'] == "Application" ]

if len(apps) == 0:
  raise Exception("Set of resources in {:s} does not include one of Application kind")
if len(apps) > 1:
  raise Exception("Set of resources in {:s} includes more than one of Application kind")

kinds = map(lambda x: x['kind'], apps[0]['spec']['componentKinds'])

excluded_kinds = [ "PersistentVolumeClaim", "Application" ]
included_kinds = [ kind for kind in kinds if kind not in excluded_kinds ]

print("Owner references not set for " + ", ".join(excluded_kinds))

with open(args.dest, "w") as outfile:
  for resource in resources:
    if resource['kind'] in included_kinds:
      print("Application '{:s}' owns '{:s}/{:s}'".format(
        args.appname, resource['kind'], resource['metadata']['name']))
      if 'metadata' not in resource:
        resource['metadata'] = {}
      if 'ownerReferences' not in resource['metadata']:
        resource['metadata']['ownerReferences'] = []

      ownerReference = {}
      ownerReference['apiVersion'] = "extensions/v1beta1"
      ownerReference['kind'] = "Application"
      ownerReference['controller'] = True # TODO(ruela) Check why we need this
      ownerReference['blockOwnerDeletion'] = True # TODO(ruela) Check why we need this
      ownerReference['name'] = args.appname
      ownerReference['uid'] = args.appuid
      resource['metadata']['ownerReferences'].append(ownerReference)

    outfile.write(docstart)
    yaml.dump(resource, outfile, default_flow_style=False)
