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
from yaml_util import overlay_yaml_file
from yaml_util import load_yaml
from yaml_util import add_or_replace

def main():
  parser = ArgumentParser()
  parser.add_argument('--orig',
                      help='Original schema file')
  parser.add_argument('--dest',
                      help='Destination schema file')
  args = parser.parse_args()

  orig = load_yaml(args.orig)

  if 'properties' not in orig:
    print("No properties found in {}. Ignoring test schema merge.".format(args.orig))
    return

  dest = load_yaml(args.dest)
  if 'properties' in dest:
    for prop in orig['properties']:
      dest['properties']['prop'] = orig['properties']['prop']
  else:
    dest['properties'] = orig['properties']
  
  with open(args.dest, 'w') as f:
    yaml.dump(dest, f)

if __name__ == "__main__":
  main()
