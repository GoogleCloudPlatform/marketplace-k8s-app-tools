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
_HOOK_SUCCESS = 'test-success'
_HOOK_FAILURE = 'test-failure'


def _has_hook(res, hook):
  if not isInstance(res, dict) or not 'metadata' in res.keys():
    return False
  metadata = res['metadata']
  if not isInstance(metadata, dict) or not 'annotations' in metadata.keys():
    return False
  annotations = metadata['annotations']
  return (isInstance(annotations, dict)
         and _HELM_HOOK_KEY in annotations.keys()
         and annotations[_HELM_HOOK_KEY] == hook)


def _is_test(res):
  return (_has_hook(res, _HOOK_SUCCESS)
         or _has_hook(res, _HOOK_FAILURE))


def _get_all_non_tests(resources):
  return filter(lambda r: not _is_test(r), resources)


def _get_all_success_tests(resources):
  return filter(lambda r: _has_hook(r, _HOOK_SUCCESS), resources)


def main():
  parser = ArgumentParser()
  parser.add_argument("-m", "--manifest", dest="manifest",
                      help="the manifest file location to be cleared of tests")
  parser.add_argument("-t", "--tests-manifest", dest="tests_manifest",
                      help="the manifest file to place all the success tests")
  args = parser.parse_args()
  manifest = args.manifest
  resources = load_resources_yaml(manifest)
  non_tests = _get_all_non_tests(resources)
  success_tests = _get_all_success_tests(resources)
  with open(manifest, "w") as out:
    yaml.dump_all(non_tests, out,
                  default_flow_style=False, explicit_start=True)
  if args.tests_manifest:
    with open(args.tests_manifest, "w") as out:
      yaml.dump_all(success_tests, out,
                    default_flow_style=False, explicit_start=True)


if __name__ == "__main__":
  main()

