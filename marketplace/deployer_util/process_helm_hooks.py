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

import yaml

from argparse import ArgumentParser
from constants import GOOGLE_CLOUD_TEST
from dict_util import deep_get
from yaml_util import load_resources_yaml
''' Remove all resources considered to be Kuberenetes Helm tests from
    a given manifest file. '''

_HELM_HOOK_KEY = 'helm.sh/hook'
_HOOK_SUCCESS = 'test-success'
_HOOK_FAILURE = 'test-failure'


def main():
  parser = ArgumentParser()
  parser.add_argument(
      "--manifest", help="the manifest file location to be cleared of tests")
  parser.add_argument(
      "--deploy_tests",
      action="store_true",
      help="indicates whether tests should be deployed")
  args = parser.parse_args()

  manifest = args.manifest
  resources = load_resources_yaml(manifest)
  filtered_resources = []
  for resource in resources:
    helm_hook = deep_get(resource, "metadata", "annotations", _HELM_HOOK_KEY)
    if helm_hook is None:
      filtered_resources.append(resource)
    elif helm_hook == _HOOK_SUCCESS:
      if args.deploy_tests:
        annotations = deep_get(resource, "metadata", "annotations")
        del annotations[_HELM_HOOK_KEY]
        annotations[GOOGLE_CLOUD_TEST] = "test"
        filtered_resources.append(resource)
    elif helm_hook == _HOOK_FAILURE:
      if args.deploy_tests:
        raise Exception("Helm hook {} is not supported".format(helm_hook))
    else:
      raise Exception("Helm hook {} is not supported".format(helm_hook))

  with open(manifest, "w", encoding='utf-8') as out:
    yaml.dump_all(
        filtered_resources, out, default_flow_style=False, explicit_start=True)


if __name__ == "__main__":
  main()
