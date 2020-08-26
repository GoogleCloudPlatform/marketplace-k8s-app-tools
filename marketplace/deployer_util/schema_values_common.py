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

import functools

import config_helper

VALUES_FILE = {
    'stdin': '-',
    'raw': '/data/values.yaml',
    'expanded': '/data/final_values.yaml',
}

VALUES_DIR = {
    'stdin': '/dev/null',
    'raw': '/data/values',
    'expanded': '/data/final_values',
}


def add_to_argument_parser(parser):
  parser.add_argument(
      '--schema_file',
      help='Path to the schema file',
      default='/data/schema.yaml')

  parser.add_argument(
      '--values_mode',
      help='"expanded" for expanded, and "raw" for not, and stdin for '
      'specified via standard in.',
      choices=VALUES_FILE.keys(),
      default='expanded')


def memoize(func):
  cache = func.cache = {}

  @functools.wraps(func)
  def memoized_func(*args, **kwargs):
    key = str(args) + str(kwargs)
    if key not in cache:
      cache[key] = func(*args, **kwargs)
    return cache[key]

  return memoized_func


@memoize
def load_schema(parsed_args):
  return config_helper.Schema.load_yaml_file(parsed_args.schema_file)


def load_schema_and_validate(parsed_args):
  return load_schema(parsed_args).validate()


@memoize
def load_values(parsed_args):
  values_file = VALUES_FILE[parsed_args.values_mode]
  values_dir = VALUES_DIR[parsed_args.values_mode]
  return config_helper.load_values(values_file, values_dir,
                                   load_schema(parsed_args))
