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

import json
import shlex
import subprocess


class CommandException(Exception):
  pass


class Command:
  """Wrapper around subprocess for simpler syntax in python code for calling other programs"""

  def __init__(self, cmd, print_call=False, print_result=False):
    if print_call:
      print(cmd)

    parsedCmd = shlex.split(cmd)
    self._process = subprocess.Popen(
        parsedCmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self._exitcode = None
    self._output = None
    self._error = None
    self._print_call = print_call
    self._print_result = print_result
    self._run()

  def jq(self, query):
    return self.pipe("jq {}".format(query))

  def pipe(self, cmd):
    if self._print_call:
      print("| " + cmd)

    parsedCmd = shlex.split(cmd)
    p2 = subprocess.Popen(
        parsedCmd,
        stdin=self._process.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    self._process = p2
    self._run()
    return self

  def _run(self):
    self._output, self._error = self._process.communicate()
    self._exitcode = self._process.returncode
    if self._print_result:
      print("result: " + str((self._exitcode, self._output, self._error)))

    if self._exitcode > 0:
      raise CommandException(self._error)

  def json(self):
    return json.loads(self._output)

  @property
  def exitcode(self):
    return self._exitcode

  @property
  def output(self):
    return self._output

  @property
  def error(self):
    return self._error
