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

import yaml

import config_helper
import print_config


class PrintConfigTest(unittest.TestCase):

  def test_load_yaml_file(self):
    schema = config_helper.Schema.load_yaml("""
        properties:
          propertyInt:
            type: int
          propertyString:
            type: string
        """)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8') as f:
      f.write("""
              propertyInt: 3
              propertyString: abc
              """)
      f.flush()

      values = config_helper.load_values(f.name, '/non/existence/dir', schema)
      self.assertEqual({'propertyInt': 3, 'propertyString': 'abc'}, values)

  def test_output_shell_vars(self):
    self.assertEqual(
        '$propertyInt $propertyString',
        print_config.output_shell_vars({
            'propertyInt': 1,
            'propertyString': 'Value'
        }))

  def test_output_yaml(self):
    values = {
        'propertyInt': 1,
        'propertyString': 'unnested',
        'dotted.propertyInt': 2,
        'dotted.propertyString': 'nested',
        'dotted.dotted.propertyInt': 3,
        'dotted.dotted.propertyString': 'double_nested',
        'dotted.dotted.dotted.propertyInt': 4,
        'dotted.dotted.dotted.propertyString': 'triple_nested',
    }
    actual = print_config.output_yaml(values)
    self.assertEqual(
        yaml.safe_load(actual), {
            'propertyInt': 1,
            'propertyString': 'unnested',
            'dotted': {
                'propertyInt': 2,
                'propertyString': 'nested',
                'dotted': {
                    'propertyInt': 3,
                    'propertyString': 'double_nested',
                    'dotted': {
                        'propertyInt': 4,
                        'propertyString': 'triple_nested',
                    },
                },
            }
        })

  def test_output_param(self):
    values = {'name': 'name-1', 'namespace': 'namespace-1'}
    schema = config_helper.Schema.load_yaml("""
        properties:
          name:
            type: string
            x-google-marketplace:
              type: NAME
          namespace:
            type: string
            x-google-marketplace:
              type: NAMESPACE
        """)
    self.assertEqual('name',
                     print_config.output_xtype(values, schema, 'NAME', True))
    self.assertEqual(
        'namespace', print_config.output_xtype(values, schema, 'NAMESPACE',
                                               True))
    self.assertEqual('name-1',
                     print_config.output_xtype(values, schema, 'NAME', False))
    self.assertEqual(
        'namespace-1',
        print_config.output_xtype(values, schema, 'NAMESPACE', False))

  def test_output_param_multiple(self):
    values = {'property1': 'Value1', 'property2': 'Value2'}
    schema = config_helper.Schema.load_yaml("""
        properties:
          image1:
            type: string
            default: gcr.io/google/busybox:1.0
            x-google-marketplace:
              type: IMAGE
          image2:
            type: string
            default: gcr.io/google/busybox:1.0
            x-google-marketplace:
              type: IMAGE
        """)
    self.assertRaises(
        print_config.InvalidParameter,
        lambda: print_config.output_xtype(values, schema, 'IMAGE', True))
