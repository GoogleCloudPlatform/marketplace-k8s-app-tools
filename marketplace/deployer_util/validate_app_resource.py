#!/usr/bin/env python3
#
# Copyright 2019 Google LLC
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from argparse import ArgumentParser

from yaml_util import load_resources_yaml
from resources import find_application_resource
import schema_values_common

_PROG_HELP = """
Extract the Application resource from the input manifests and validate
its correctness, such as Marketplace partner and solution ID annotations,
application version and its declared value in the schema.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument(
      '--manifests',
      required=True,
      help='The yaml file containing all resources')
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  resources = load_resources_yaml(args.manifests)

  app = find_application_resource(resources)
  mp_deploy_info = app.get('metadata', {}).get(
      'annotations', {}).get('marketplace.cloud.google.com/deploy-info')
  if not mp_deploy_info:
    raise Exception('Application resource is missing '
                    '"marketplace.cloud.google.com/deploy-info" annotation')

  version = app.get('spec', {}).get('descriptor', {}).get('version')
  if not version or not isinstance(version, str):
    raise Exception(
        'Application resource must have a valid spec.descriptor.version value')
  if schema.is_v2():
    published_version = schema.x_google_marketplace.published_version
    if version != published_version:
      raise Exception(
          'Application resource\'s spec.descriptor.version "{}" does not match '
          'schema.yaml\'s publishedVersion "{}"'.format(version,
                                                        published_version))


if __name__ == "__main__":
  main()
