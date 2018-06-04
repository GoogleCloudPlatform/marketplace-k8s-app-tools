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
from constants import GOOGLE_CLOUD_TEST
from dict_util import deep_get
from yaml_util import load_resources_yaml


''' Convert the helm tests into google-marketplace tests. '''


_HELM_HOOK_KEY = 'helm.sh/hook'
_HOOK_SUCCESS = 'test-success'


def main():
  parser = ArgumentParser()
  parser.add_argument("--manifest", dest="manifest",
                      help="the manifest file location to be cleared of tests")
  args = parser.parse_args()
  manifest = args.manifest
  resources = load_resources_yaml(manifest)
  for resource in resources:
    helm_hook = deep_get(resource, "metadata", "annotations", _HELM_HOOK_KEY)
    if helm_hook is None:
      continue

    if helm_hook == _HOOK_SUCCESS:
      annotations = deep_get(resource, "metadata", "annotations")
      del annotations[_HELM_HOOK_KEY]
      annotations[GOOGLE_CLOUD_TEST] = "test"
    else:
      raise Exception("Helm hook {} is not supported".format(helm_hook))

  with open(manifest, "w") as out:
    yaml.dump_all(resources, out,
                  default_flow_style=False, explicit_start=True)


if __name__ == "__main__":
  main()

