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

from argparse import ArgumentParser
import os
import re
import subprocess
import sys
import yaml


_PROG_HELP = """
Outputs configuration parameters constructed from files in a directory.
The file names are parameter names, file contents parameter values.
The program supports several output formats, controlled by --output.
"""

_OUTPUT_HELP = """
Choose the format to output paremeter name-value pair.
shell: lines of VAR=VALUE, where the VALUEs are properly shell escaped.
yaml: a YAML file.
"""

OUTPUT_SHELL = 'shell'
OUTPUT_YAML = 'yaml'
CODEC_UTF8 = 'UTF-8'
CODEC_ASCII = 'ASCII'

NAME_RE=re.compile(r'[a-zA-z0-9_]+$')


class InvalidName(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--output', '-o', help=_OUTPUT_HELP,
                      choices=[OUTPUT_SHELL, OUTPUT_YAML],
                      default=OUTPUT_SHELL)
  parser.add_argument('--values_dir', help='Where to read value files',
                      default='/data/values')
  parser.add_argument('--param',
                      help='If specified, outputs the value of a single '
                      'parameter, unescaped.')
  parser.add_argument('--decoding',
                      help='Codec used for decoding value file contents',
                      choices=[CODEC_UTF8, CODEC_ASCII], default='UTF-8')
  parser.add_argument('--encoding',
                      help='Codec for encoding output files',
                      choices=[CODEC_UTF8, CODEC_ASCII], default='UTF-8')
  args = parser.parse_args()

  values = read_values_to_dict(args.values_dir, args.decoding)

  try:
    if args.param:
      if args.param in values:
        sys.stdout.write(values[args.param])
      else:
        raise InvalidName('No such parameter: {}\n'.format(args.param))
      return

    if args.output == OUTPUT_SHELL:
      sys.stdout.write(output_shell(values))
    elif args.output == OUTPUT_YAML:
      sys.stdout.write(output_yaml(values, args.encoding))
  finally:
    sys.stdout.flush()


def read_values_to_dict(values_dir, codec):
  """Returns a dict construted from files in values_dir."""
  files = [f for f in os.listdir(values_dir)
           if os.path.isfile(os.path.join(values_dir, f))]
  result = {}
  for filename in files:
    if not NAME_RE.match(filename):
      raise InvalidName('Invalid config parameter name: {}'.format(filename))
    file_path = os.path.join(values_dir, filename)
    with open(file_path, "r") as f:
      data = f.read().decode(codec)
      result[filename] = data
  return result


def output_shell(values):
  escapeds = [
      (k, subprocess.check_output(['printf', '%q', v], env=values))
      for k, v in values.iteritems()]
  escapeds.sort(key=lambda (k, v): k)
  return '\n'.join(['{}={}'.format(k, v) for k, v in escapeds])


def output_yaml(values, encoding):
  return yaml.safe_dump(values,
                        encoding=encoding,
                        default_flow_style=False,
                        indent=2)


if __name__ == "__main__":
  main()
