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
import sys
from argparse import ArgumentParser

import yaml

from yaml_util import load_resources_yaml
from yaml_util import parse_resources_yaml

_PROG_HELP = """
Sets the app.kubernetes.io labels on resources.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument(
      "--manifests",
      help="The folder containing the manifest templates, "
      "or - to read from stdin",
      required=True)
  parser.add_argument(
      "--dest",
      help="The output file for the resulting manifest, "
      "or - to write to stdout",
      required=True)
  parser.add_argument(
      "--name", help="The name of the application instance", required=True)
  parser.add_argument(
      "--namespace",
      help="The namespace where the application is installed",
      required=True)
  args = parser.parse_args()

  resources = []
  if args.manifests == "-":
    resources = parse_resources_yaml(sys.stdin.read())
  elif os.path.isfile(args.manifests):
    resources = load_resources_yaml(args.manifests)
  else:
    resources = []
    for filename in os.listdir(args.manifests):
      resources += load_resources_yaml(os.path.join(args.manifests, filename))

  # Modify resources inlined.
  for resource in resources:
    labels = resource['metadata'].get('labels', {})
    resource['metadata']['labels'] = labels
    labels['app.kubernetes.io/name'] = args.name
    # For a resource that doesn't have a namespace (i.e. cluster resource),
    # also all label it with the namespace of the application.
    if 'namespace' not in resource['metadata']:
      labels['app.kubernetes.io/namespace'] = args.namespace

  if args.dest == "-":
    write_resources(resources, sys.stdout)
    sys.stdout.flush()
  else:
    with open(args.dest, "w", encoding='utf-8') as outfile:
      write_resources(resources, outfile)


def write_resources(resources, outfile):
  yaml.safe_dump_all(resources, outfile, default_flow_style=False, indent=2)


if __name__ == "__main__":
  main()
