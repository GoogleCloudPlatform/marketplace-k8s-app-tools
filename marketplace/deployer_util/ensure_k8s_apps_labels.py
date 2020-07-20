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
import copy

from argparse import ArgumentParser
from yaml_util import load_resources_yaml

_K8S_APP_LABEL_KEY = 'app.kubernetes.io/name'


def ensure_resource_has_app_label(resource, app_name):
  res = copy.deepcopy(resource)
  metadata = res.get('metadata', {})
  res['metadata'] = metadata
  labels = metadata.get('labels', {})
  metadata['labels'] = labels
  if not _K8S_APP_LABEL_KEY in labels.keys():
    labels[_K8S_APP_LABEL_KEY] = app_name
  return res


def main():
  parser = ArgumentParser()
  parser.add_argument(
      "-m",
      "--manifest",
      dest="manifest",
      help="the manifest file to be parsed and updated")
  parser.add_argument(
      "-a",
      "--appname",
      dest="application_name",
      help="the application instance name")
  args = parser.parse_args()
  manifest = args.manifest
  app_name = args.application_name
  resources = load_resources_yaml(manifest)
  resources = [ensure_resource_has_app_label(r, app_name) for r in resources]
  with open(manifest, "w", encoding='utf-8') as out:
    yaml.dump_all(resources, out, default_flow_style=False, explicit_start=True)


if __name__ == "__main__":
  main()
