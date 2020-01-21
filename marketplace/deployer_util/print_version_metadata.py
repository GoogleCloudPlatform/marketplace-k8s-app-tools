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

import collections
import datetime
import sys
import yaml

from argparse import ArgumentParser

import schema_values_common

_PROG_HELP = """
Generates a version metadata in yaml format from schema.yaml.
Requires schema.yaml version v2.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument(
      '--deployer_image',
      required=True,
      help='The full deployer image, required')
  parser.add_argument(
      '--deployer_image_digest',
      required=True,
      help='The digest of the deployer image, required')
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  schema.validate()
  if (schema.x_google_marketplace is None or
      not schema.x_google_marketplace.is_v2()):
    raise Exception('schema.yaml must be in v2 version')

  x = schema.x_google_marketplace
  meta = collections.OrderedDict([
      ('releaseDate', _utcnow_timestamp()),
      ('url', args.deployer_image),
      ('digest', args.deployer_image_digest),
      ('releaseNote', x.published_version_meta.release_note),
  ])
  if x.published_version_meta.release_types:
    meta['releaseTypes'] = x.published_version_meta.release_types
  if x.published_version_meta.recommended is not None:
    meta['recommended'] = x.published_version_meta.recommended

  sys.stdout.write(_ordered_dump(meta, default_flow_style=False, indent=2))
  sys.stdout.flush()


def _ordered_dump(data, stream=None, dumper=yaml.Dumper, **kwds):

  class OrderedDumper(dumper):
    pass

  def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

  OrderedDumper.add_representer(collections.OrderedDict, _dict_representer)
  return yaml.dump(data, stream, OrderedDumper, **kwds)


def _utcnow_timestamp():
  # Instructed to output timezone, python would outputs +00:00 instead of Z.
  # So we add that manually here.
  return '{}Z'.format(
      datetime.datetime.utcnow().replace(microsecond=0).isoformat())


if __name__ == "__main__":
  main()
