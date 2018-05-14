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

import yaml

import config_helper
import print_config


class PrintConfigTest(unittest.TestCase):
  def test_output_shell_vars(self):
    self.assertEqual(
        '$propertyInt $propertyString',
        print_config.output_shell_vars({'propertyInt': 1,
                                        'propertyString': 'Value'}))

  def test_output_yaml(self):
    values = {'propertyInt': 1,
              'propertyString': 'Value',
              'dotted.propertyInt': 2,
              'dotted.propertyString': 'DottedValue'}
    actual = print_config.output_yaml(values, 'utf_8')
    expected = ['dotted:',
                '  propertyInt: 2',
                '  propertyString: DottedValue',
                'propertyInt: 1',
                'propertyString: Value',
                '']
    self.assertEquals(actual.split('\n'), expected)

  def test_output_param(self):
    values = {'propertyInt': 1,
              'propertyString': 'Value'}
    schema = config_helper.Schema.load_yaml(
        """
        properties:
          propertyInt:
            type: int
          propertyString:
            type: string
        """)
    self.assertEqual('1',
                     print_config.output_param(values, schema,
                                               {'name': 'propertyInt'}))
    self.assertEqual('Value',
                     print_config.output_param(values, schema,
                                               {'name': 'propertyString'}))

  def test_output_param_multiple(self):
    values = {'property1': 'Value1',
              'property2': 'Value2'}
    schema = config_helper.Schema.load_yaml(
        """
        properties:
          property1:
            type: string
          property2:
            type: string
        """)
    self.assertRaises(
        print_config.InvalidParameter,
        lambda: print_config.output_param(values, schema, {'type': 'string'}))
