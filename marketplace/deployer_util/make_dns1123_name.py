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

import hashlib
import re
from argparse import ArgumentParser

import six

_PROG_HELP = """
Turns a name into a proper DNS-1123 subdomain, with limitations.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--name', required=True)
  args = parser.parse_args()

  print(dns1123_name(args.name))


def dns1123_name(name):
  """Turns a name into a proper DNS-1123 subdomain.

  This does NOT work on all names. It assumes the name is mostly correct
  and handles only certain situations.
  """
  # Attempt to fix the input name.
  fixed = name.lower()
  fixed = re.sub(r'[.]', '-', fixed)
  fixed = re.sub(r'[^a-z0-9-]', '', fixed)
  fixed = fixed.strip('-')
  fixed = limit_name(fixed, 64)
  return fixed


def limit_name(name, length=127):
  result = name
  if len(result) > length:
    result = result[:length - 5]
    # Hash and get the first 4 characters of the hash.
    m = hashlib.sha256()
    m.update(six.ensure_binary(name, 'utf-8'))
    h4sh = m.hexdigest()[:4]
    result = '{}-{}'.format(result, h4sh)
  return result


if __name__ == "__main__":
  main()
