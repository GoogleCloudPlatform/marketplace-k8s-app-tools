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

import yaml

from argparse import ArgumentParser
from yaml_util import load_resources_yaml


''' Remove all resources considered to be Kuberenetes Helm tests from
    a given manifest file. '''


_HELM_HOOK_KEY = 'helm.sh/hook'
_HELM_TEST_HOOKS = ['test-success', 'test-failure']


def is_resource_a_helm_test(res):
  if not type(res) is dict \
      or not 'metadata' in res.keys():
    return False
  metadata = res['metadata']
  if not type(metadata) is dict \
      or not 'annotations' in metadata.keys():
    return False
  annotations = metadata['annotations']
  return type(annotations) is dict \
         and _HELM_HOOK_KEY in annotations.keys() \
         and annotations[_HELM_HOOK_KEY] in _HELM_TEST_HOOKS


def main():
  parser = ArgumentParser()
  parser.add_argument("-m", "--manifest", dest="manifest",
                      help="the manifest file location to be cleared of tests")
  args = parser.parse_args()
  manifest = args.manifest
  resources = load_resources_yaml(manifest)
  resources = filter(lambda r: not is_resource_a_helm_test(r), resources)
  with open(manifest, "w") as out:
    yaml.dump_all(resources, out, default_flow_style=False, explicit_start=True)
  print "FILTER-OUT procedure for Helm tests finished"


if __name__ == "__main__":
  main()