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

import subprocess
import sys
from argparse import ArgumentParser

import schema_values_common

_PROG_HELP = """
Runs a specified command within an environment with env variables
setup from the config parameters.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument('command', help='Command to run')
  parser.add_argument('arguments', nargs='*', help='Arguments to the command')
  args = parser.parse_args()

  values = schema_values_common.load_values(args)
  # Convert values to strings to pass to subprocess.
  values = {k: str(v) for k, v in values.items()}

  # Default env vars should NOT be passed on to the new environment.
  default_vars = [
      v.decode('utf-8').split('=')[0] for v in subprocess.check_output(
          ['env -0'], env={}, shell=True).split(b'\0') if v
  ]
  command = (['/usr/bin/env'] + ['--unset={}'.format(v) for v in default_vars] +
             [args.command] + args.arguments)
  p = subprocess.Popen(
      command,
      env=values,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)
  stdoutdata, stderrdata = p.communicate(input=sys.stdin.buffer.read())
  if stdoutdata:
    sys.stdout.buffer.write(stdoutdata)
    sys.stdout.flush()
  if stderrdata:
    sys.stderr.buffer.write(stderrdata)
    sys.stderr.flush()
  sys.exit(p.returncode)


if __name__ == "__main__":
  main()
