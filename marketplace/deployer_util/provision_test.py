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

import unittest

import provision
from provision import dns1123_name
from provision import limit_name

import config_helper


class ProvisionTest(unittest.TestCase):

  def test_dns1123_name(self):
    self.assertEqual(dns1123_name('valid-name'), 'valid-name')
    self.assertEqual(dns1123_name('aA'), 'aa')
    self.assertEqual(
        dns1123_name('*sp3cial-@chars.(rem0ved^'), 'sp3cial-chars-rem0ved')
    self.assertEqual(dns1123_name('-abc.def.'), 'abc-def')
    self.assertEqual(dns1123_name('-123.456.'), '123-456')
    self.assertModifiedName(
        dns1123_name('Lorem-Ipsum-is-simply-dummy-text-of-the-printing-and-'
                     'typesettings-----------------------------------------'),
        'lorem-ipsum-is-simply-dummy-text-of-the-printing-and-typese')
    self.assertModifiedName(
        dns1123_name('Lorem-Ipsum-is-simply-dummy-text-of-the-printing-and-'
                     'typesettings.........................................'),
        'lorem-ipsum-is-simply-dummy-text-of-the-printing-and-typese')

  def test_limit_name(self):
    self.assertEqual(limit_name('valid-name'), 'valid-name')
    self.assertEqual(limit_name('valid-name', 8), 'val-030a')

  def assertModifiedName(self, text, expected):
    self.assertEqual(text[:-5], expected)
    self.assertRegexpMatches(text[-5:], r'-[a-f0-9]{4}')

  def test_deployer_image_inject(self):
    schema = config_helper.Schema.load_yaml('''
    properties:
      deployer_image:
        type: string
        x-google-marketplace:
          type: DEPLOYER_IMAGE
    ''')
    values = {}
    deployer_image = 'gcr.io/cloud-marketplace/partner/solution/deployer:latest'
    self.assertEquals(
        provision.inject_deployer_image_properties(
            values, schema, deployer_image), {"deployer_image": deployer_image})
