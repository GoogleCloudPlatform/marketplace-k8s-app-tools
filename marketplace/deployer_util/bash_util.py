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

import six


class CommandException(Exception):

  def __init__(self, exitcode, message):
    self._exitcode = exitcode
    super(Exception, self).__init__(message)

  @property
  def exitcode(self):
    return self._exitcode


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
    self._print_call = print_call
    self._print_result = print_result
    self._run()

  def _run(self):
    self._output, error_message = self._process.communicate()
    self._output = six.ensure_str(self._output, 'utf-8')
    error_message = six.ensure_str(error_message, 'utf-8')
    self._exitcode = self._process.returncode
    if self._print_result:
      print("result: " + str((self._exitcode, self._output, error_message)))

    if self._exitcode > 0:
      raise CommandException(self._exitcode, error_message)

  def json(self):
    return json.loads(self._output)

  @property
  def exitcode(self):
    return self._exitcode

  @property
  def output(self):
    return self._output
