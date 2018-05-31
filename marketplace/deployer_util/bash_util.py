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
      print cmd

    parsedCmd = shlex.split(cmd)
    self.process = subprocess.Popen(parsedCmd,
      stdin=None,
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE)
    self.exitcode = None
    self.output = None
    self.error = None
    self.print_call = print_call
    self.print_result = print_result


  def jq(self, query):
    return self.p("jq {}".format(query))


  def p(self, cmd):
    if self.print_call:
      print "| " + cmd

    parsedCmd = shlex.split(cmd)

    p2 = subprocess.Popen(parsedCmd, 
      stdin=self.process.stdout, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE)

    self.process = p2
    return self


  def text(self):
    if not self.exitcode:
      self.output, self.error = self.process.communicate()
      self.exitcode = self.process.returncode

    if self.print_result:
      print "result: " + str((self.exitcode, self.output, self.error))

    if self.exitcode > 0:
      raise CommandException(self.error)

    return self.output


  def json(self):
    return json.loads(self.text())
