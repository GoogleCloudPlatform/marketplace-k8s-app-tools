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

import config_helper
import contextlib
import expand_config
import re
import shutil
import tempfile
import unittest


class ExpandConfigTest(unittest.TestCase):
  def test_defaults(self):
    schema = config_helper.Schema.load_yaml(
        """
        properties:
          p1:
            type: string
            default: Default
        """)
    self.assertEqual({'p1': 'Default'},
                     expand_config.expand({}, schema))
    self.assertEqual({'p1': 'Mine'},
                     expand_config.expand({'p1': 'Mine'}, schema))

  def test_invalid_value_type(self):
    schema = config_helper.Schema.load_yaml(
        """
        properties:
          p1:
            type: string
        """)
    self.assertRaises(
        expand_config.InvalidProperty,
        lambda: expand_config.expand({'p1': 3}, schema))

  def test_generate_password(self):
    schema = config_helper.Schema.load_yaml(
        """
        properties:
          p1:
            type: string
            x-google-marketplace:
              type: GENERATED_PASSWORD
              generatedPassword:
                length: 8
                includeSymbols: false
                base64: false
        """)
    result = expand_config.expand({}, schema)
    self.assertEqual({'p1'}, set(result))
    self.assertIsNotNone(re.match(r'^[a-zA-Z0-9]{8}$', result['p1']))

  def test_write_values(self):
    schema = config_helper.Schema.load_yaml(
        """
        properties:
          propertyInt:
            type: int
          propertyStr:
            type: string
          propertyNum:
            type: number
        """)
    values = {'propertyInt': 4, 'propertyStr': 'Value', 'propertyNum': 1.0}
    with tempdir() as dir_path:
      expand_config.write_values(values, dir_path, encoding='utf_8')
      actual = config_helper.read_values_to_dict(dir_path, 'utf_8', schema)
      self.assertEqual(values, actual)


@contextlib.contextmanager
def tempdir():
  dir_path = tempfile.mkdtemp()
  try:
    yield dir_path
  finally:
    shutil.rmtree(dir_path)
