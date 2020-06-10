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

import sys


def info(msg, *args):
  log("INFO " + msg, *args)


def warn(msg, *args):
  log("WARNING " + msg, *args)


def error(msg, *args):
  log("ERROR " + msg, *args)


def log(msg, *args):
  sys.stderr.write(msg.format(*args))
  sys.stderr.write('\n')
  sys.stderr.flush()
