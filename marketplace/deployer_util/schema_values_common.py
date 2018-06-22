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

CODEC_ASCII = 'ascii'
CODEC_UTF8 = 'utf_8'


def add_to_argument_parser(parser,
                           values_file='/data/final_values.yaml',
                           values_dir='/data/final_values'):
  parser.add_argument('--values_file',
                      help='Yaml file to read values from. Takes precendence '
                      'over --values_dir if the file exists. '
                      'Use "-" to specify reading from stdin',
                      default=values_file)
  parser.add_argument('--values_dir',
                      help='Where to read value files',
                      default=values_dir)
  parser.add_argument('--values_dir_encoding',
                      help='Encoding of --values_dir file contents',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  parser.add_argument('--schema_file', help='Path to the schema file',
                      default='/data/schema.yaml')


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


@memoize
def load_values(parsed_args):
  return config_helper.load_values(parsed_args.values_file,
                                   parsed_args.values_dir,
                                   parsed_args.values_dir_encoding,
                                   load_schema(parsed_args))
