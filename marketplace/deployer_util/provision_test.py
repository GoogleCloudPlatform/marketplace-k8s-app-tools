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

import tempfile
import unittest

from provision import dns1123_name


class ProvisionTest(unittest.TestCase):

  def test_dns1123_name(self):
    self.assertEqual(dns1123_name('valid-name'),
                     'valid-name')
    self.assertModifiedName(dns1123_name('aA'),
                            'aa')
    self.assertModifiedName(dns1123_name('*sp3cial-@chars.(rem0ved^'),
                            'sp3cial-chars-rem0ved')
    self.assertModifiedName(dns1123_name('-abc.def.'),
                            'abc-def')
    self.assertModifiedName(dns1123_name('-123.456.'),
                            '123-456')
    self.assertModifiedName(
        dns1123_name('very-long-Name-that-gets-chopped-at-a-dash-'
                     '-------------------------------------------'),
        'very-long-name-that-gets-chopped-at-a-dash')
    self.assertModifiedName(
        dns1123_name('very-long-Name-that-gets-chopped-at-a-dot-'
                     '...........................................'),
        'very-long-name-that-gets-chopped-at-a-dot')

  def assertModifiedName(self, text, expected):
    self.assertEqual(text[:-5], expected)
    self.assertRegexpMatches(text[-5:],
                             r'-[a-f0-9]{4}')
