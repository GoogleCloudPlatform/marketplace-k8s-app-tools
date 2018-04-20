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
import subprocess
import sys
import yaml


PROG_HELP = """
Outputs configuration parameters constructed from files in a directory.
The file names are parameter names, file contents parameter values.
The program supports several output formats, controlled by --output.
"""

OUTPUT_SHELL = 'shell'
OUTPUT_YAML = 'yaml'
CODEC_UTF8 = 'UTF-8'
CODEC_ASCII = 'ASCII'


def main():
  parser = ArgumentParser(description=PROG_HELP)
  parser.add_argument('--output', '-o',
                      choices=[OUTPUT_SHELL, OUTPUT_YAML], default=OUTPUT_SHELL)
  parser.add_argument('--values_dir', default='/data/values')
  parser.add_argument('--decoding',
                      choices=[CODEC_UTF8, CODEC_ASCII], default='UTF-8')
  parser.add_argument('--encoding',
                      choices=[CODEC_UTF8, CODEC_ASCII], default='UTF-8')
  parser.add_argument('--no_newline', '-n',
                      help='Do not include a newline at the end',
                      action='store_true')
  args = parser.parse_args()

  values = read_values_to_dict(args.values_dir, args.decoding)
  if args.output == OUTPUT_SHELL:
    sys.stdout.write(output_shell(values, args.no_newline))
  elif args.output == OUTPUT_YAML:
    sys.stdout.write(output_yaml(values, args.encoding))
  sys.stdout.flush()


def read_values_to_dict(values_dir, codec):
  """Returns a dict construted from files in values_dir."""
  files = [f for f in os.listdir(values_dir)
           if os.path.isfile(os.path.join(values_dir, f))]
  result = {}
  for filename in files:
    file_path = os.path.join(values_dir, filename)
    with open(file_path, "r") as f:
      data = f.read().decode(codec)
      result[filename] = data
  return result


def output_shell(values, no_newline):
  # Utilize shell's export builtin to properly print out all env variables.
  # There are a few exports included by default, so we want to exclude
  # them. Taking advantage of the fact export keeps order of the variables,
  # we can simply skip the first N default env variables.
  default_exports_count = len(
      subprocess.check_output(['export'], env={}, shell=True)
      .splitlines())
  all_exports = (
      subprocess.check_output(['export'], env=values, shell=True)
      .splitlines())
  exports = all_exports[default_exports_count:]
  if not no_newline:
    exports.append('')
  return '\n'.join(exports)


def output_yaml(values, encoding):
  return yaml.safe_dump(values,
                        encoding=args.encoding,
                        default_flow_style=False,
                        indent=2)


if __name__ == "__main__":
  main()
