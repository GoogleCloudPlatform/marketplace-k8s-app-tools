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

from argparse import ArgumentParser
from resources import set_resource_ownership
from yaml_util import load_resources_yaml
from yaml_util import docstart

_PROG_HELP = """
Scans the manifest folder kubernetes resources and set the Application to own
the ones defined in its list of components kinds.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument("--appname", help="the name of the applictation instance")
  parser.add_argument("--appuid", help="the uid of the applictation instance")
  parser.add_argument("--manifests", help="the folder containing the manifest templates")
  parser.add_argument("--dest", help="the output file for the resulting manifest")
  args = parser.parse_args()

  resources = []
  for filename in os.listdir(args.manifests):
    docs = load_resources_yaml(os.path.join(args.manifests, filename))
    map(lambda doc: resources.append(doc), docs)

  apps = [ r for r in resources if r['kind'] == "Application" ]

  if len(apps) == 0:
    raise Exception("Set of resources in {:s} does not include one of Application kind".format(args.manifests))
  if len(apps) > 1:
    raise Exception("Set of resources in {:s} includes more than one of Application kind".format(args.manifests))

  kinds = map(lambda x: x['kind'], apps[0]['spec']['componentKinds'])

  excluded_kinds = [ "PersistentVolumeClaim", "Application" ]
  included_kinds = [ kind for kind in kinds if kind not in excluded_kinds ]

  print("Owner references not set for " + ", ".join(excluded_kinds))

  with open(args.dest, "w") as outfile: 
    for resource in resources:
      if resource['kind'] in included_kinds:
        print("Application '{:s}' owns '{:s}/{:s}'".format(
          args.appname, resource['kind'], resource['metadata']['name']))
        set_resource_ownership(args.appuid, args.appname, resource)
      outfile.write(docstart)
      yaml.dump(resource, outfile, default_flow_style=False)    


if __name__ == "__main__":
  main()
