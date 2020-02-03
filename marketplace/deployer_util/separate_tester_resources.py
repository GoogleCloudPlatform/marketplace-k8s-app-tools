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

from argparse import ArgumentParser
from constants import GOOGLE_CLOUD_TEST
from dict_util import deep_get
from resources import set_app_resource_ownership
from yaml_util import load_resources_yaml

_PROG_HELP = "Separate the tester job from resources manifest into a different manifest"


def main():

  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument(
      "--app_name", required=True, help="the name of the application instance")
  parser.add_argument(
      "--app_uid", required=True, help="the uid of the application instance")
  parser.add_argument(
      "--app_api_version",
      required=True,
      help="apiVersion of the Application CRD")
  parser.add_argument(
      "--manifests", required=True, help="the configuration for tests")
  parser.add_argument(
      "--out_manifests",
      required=True,
      help="the file to write non-test resources to")
  parser.add_argument(
      "--out_test_manifests",
      required=True,
      help="the file to write test resources to")
  args = parser.parse_args()

  if os.path.isfile(args.manifests):
    resources = load_resources_yaml(args.manifests)
  else:
    resources = []
    for filename in os.listdir(args.manifests):
      resources += load_resources_yaml(os.path.join(args.manifests, filename))

  test_resources = []
  nontest_resources = []
  for resource in resources:
    full_name = "{}/{}".format(resource['kind'],
                               deep_get(resource, 'metadata', 'name'))
    if deep_get(resource, 'metadata', 'annotations',
                GOOGLE_CLOUD_TEST) == 'test':
      print("INFO Tester resource: {}".format(full_name))
      set_app_resource_ownership(
          app_uid=args.app_uid,
          app_name=args.app_name,
          app_api_version=args.app_api_version,
          resource=resource)
      test_resources.append(resource)
    else:
      print("INFO Prod resource: {}".format(full_name))
      nontest_resources.append(resource)

  if nontest_resources:
    with open(args.out_manifests, "w", encoding='utf-8') as outfile:
      yaml.safe_dump_all(nontest_resources, outfile, default_flow_style=False)

  if test_resources:
    with open(args.out_test_manifests, "a", encoding='utf-8') as test_outfile:
      yaml.safe_dump_all(test_resources, test_outfile, default_flow_style=False)


if __name__ == "__main__":
  main()
