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

import subprocess
import sys
from argparse import ArgumentParser

import config_helper

_PROG_HELP = """
Runs a specified command within an environment with env variables
setup from the config parameters.
"""

CODEC_UTF8 = 'UTF-8'
CODEC_ASCII = 'ASCII'


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--values_dir',
                      help='Where the value files should be read from',
                      default='/data/final_values')
  parser.add_argument('--encoding',
                      help='Encoding of the value files',
                      choices=[CODEC_UTF8, CODEC_ASCII], default='UTF-8')
  parser.add_argument('--schema_file', help='Path to the schema file',
                      default='/data/schema.yaml')
  parser.add_argument('--schema_file_encoding',
                      help='Encoding of the schema file',
                      choices=[CODEC_UTF8, CODEC_ASCII], default=CODEC_UTF8)
  parser.add_argument('command', help='Command to run')
  parser.add_argument('arguments', nargs='*', help='Arguments to the command')
  args = parser.parse_args()

  schema = config_helper.Schema.load_yaml_file(args.schema_file,
                                               args.schema_file_encoding)
  values = config_helper.read_values_to_dict(args.values_dir,
                                             args.encoding,
                                             schema)
  # Convert values to strings to pass to subprocess.
  values = {k: str(v) for k, v in values.iteritems()}

  # Default env vars should NOT be passed on to the new environment.
  default_vars = [v.split('=')[0]
                  for v in subprocess.check_output(['env -0'],
                                                   env={},
                                                   shell=True).split('\0')
                  if v]
  command = (['/usr/bin/env'] +
             ['--unset={}'.format(v) for v in default_vars] +
             [args.command] +
             args.arguments)
  p = subprocess.Popen(command,
                       env=values,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
  stdoutdata, stderrdata = p.communicate(input=sys.stdin.read())
  if stdoutdata:
    sys.stdout.write(stdoutdata)
    sys.stdout.flush()
  if stderrdata:
    sys.stderr.write(stderrdata)
    sys.stderr.flush()
  sys.exit(p.returncode)


if __name__ == "__main__":
  main()
