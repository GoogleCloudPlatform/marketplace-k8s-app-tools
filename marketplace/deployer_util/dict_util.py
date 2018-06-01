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

class DictWalker:
  """ Wrapper class for dictionary which allows nested access through null object 
      Example:
      d['a.b'] raises Exception if key 'a' is not present 
      With DictWalker, the same case above returns None instead. """

  def __init__(self, d):
    self._dict = d

  def traverse(self, keys):
    if self._dict is None:
      return None

    d = self._dict
    i = 0
    for k in keys:
      if k not in d:
        return None

      d = d[k]
      if i == len(keys) - 1:
        return d

      if type(d) is not dict:
        return None

      i += 1

    if type(d) is dict:
      return DictWalker(d)

    return d

  def __getitem__(self, key):
    if self._dict is None:
      return None

    if type(key) is list:
      return self.traverse(key)

    return self._dict[key]

  def __str__(self):
     return str(self._dict)

  @property
  def dict(self):
    return self._dict
