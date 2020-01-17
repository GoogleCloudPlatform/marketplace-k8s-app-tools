# Copyright 2019 Google LLC
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

import config_helper
from validate_app_resource import validate_deploy_info_annotation


class ValidateAppResourceTest(unittest.TestCase):

  def test_deploy_info_must_be_json(self):
    self.assertRaisesRegex(
        Exception, r'.*must be valid JSON.*',
        lambda: validate_deploy_info_annotation('invalid json'))

  def test_deploy_info_must_contain_partner_id(self):
    self.assertRaisesRegex(
        Exception, r'.*must contain a partner_id.*',
        lambda: validate_deploy_info_annotation('{"product_id": "solution"}'))

  def test_deploy_info_must_contain_product_id(self):
    self.assertRaisesRegex(
        Exception, r'.*must contain a product_id.*',
        lambda: validate_deploy_info_annotation('{"partner_id": "partner"}'))

  def test_deploy_info_must_match_schema(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2
          partnerId: partner-a
          solutionId: solution-a
          applicationApiVersion: v1beta1
          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
          images: {}
        properties: {}
        """)
    self.assertRaisesRegex(
        Exception, r'Partner or solution ID values.*schema.*not consistent',
        lambda: validate_deploy_info_annotation(
            '{"partner_id": "partner-a", "product_id": "solution-b"}', schema))
    self.assertRaisesRegex(
        Exception, r'Partner or solution ID values.*schema.*not consistent',
        lambda: validate_deploy_info_annotation(
            '{"partner_id": "partner-b", "product_id": "solution-a"}', schema))
    validate_deploy_info_annotation(
        '{"partner_id": "partner-a", "product_id": "solution-a"}', schema)

  def test_deploy_info_ok_if_schema_has_no_partner_product_ids(self):
    schema = config_helper.Schema.load_yaml("""
        x-google-marketplace:
          schemaVersion: v2
          applicationApiVersion: v1beta1
          publishedVersion: 6.5.130-metadata
          publishedVersionMetadata:
            releaseNote: Bug fixes
          images: {}
        properties: {}
        """)
    validate_deploy_info_annotation(
        '{"partner_id": "partner-a", "product_id": "solution-a"}', schema)
