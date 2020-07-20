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

from resources import find_application_resource
from resources import set_app_resource_ownership
from resources import set_resource_ownership
from resources import set_service_account_resource_ownership

APP_API_VERSION = 'v1beta1'
APP_NAME = 'wordpress-1'
APP_UID = '00000000-1111-2222-3333-444444444444'
OTHER_UID = '99999999-9999-9999-9999-999999999999'
APP_OWNER_REF = {
    'apiVersion': APP_API_VERSION,
    'kind': 'Application',
    'blockOwnerDeletion': True,
    'name': APP_NAME,
    'uid': APP_UID,
}


class ResourcesTest(unittest.TestCase):

  def test_resource_existing_app_ownerref_matching_uid_updates_existing(self):
    resource = {'metadata': {'ownerReferences': [{'uid': APP_UID}]}}

    set_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, 'Application',
                           resource)
    self.assertCountEqual(resource['metadata']['ownerReferences'],
                          [APP_OWNER_REF])

  def test_resource_existing_ownerref_different_uid_adds_ownerref(self):
    resource = {'metadata': {'ownerReferences': [{'uid': OTHER_UID}]}}

    set_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, 'Application',
                           resource)
    self.assertCountEqual(resource['metadata']['ownerReferences'], [{
        'uid': OTHER_UID
    }, APP_OWNER_REF])

  def test_resource_no_ownerrefs_ownerref(self):
    resource = {'metadata': {'ownerReferences': []}}

    set_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, 'Application',
                           resource)

    self.assertCountEqual(resource['metadata']['ownerReferences'],
                          [APP_OWNER_REF])

  def test_app_resource_ownership(self):
    resource = {'metadata': {'ownerReferences': []}}

    set_app_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, resource)

    self.assertCountEqual(resource['metadata']['ownerReferences'],
                          [APP_OWNER_REF])

  def test_service_account_resource_ownership(self):
    resource = {'metadata': {'ownerReferences': []}}

    set_service_account_resource_ownership(
        '11111111-2222-3333-4444-555555555555', 'test-sa', resource)

    self.assertCountEqual(resource['metadata']['ownerReferences'], [{
        'apiVersion': 'v1',
        'kind': 'ServiceAccount',
        'blockOwnerDeletion': True,
        'name': 'test-sa',
        'uid': '11111111-2222-3333-4444-555555555555',
    }])

  def test_find_application_resource(self):
    expected_app_resource = {
        # Intentionally some version we don't support,
        # but the api group should suffice.
        'apiVersion': 'app.k8s.io/v9999',
        'kind': 'Application',
    }
    resources = [
        {
            'apiVersion': 'v1',
            'kind': 'ServiceAccount',
        },
        {
            'apiVersion': 'application.mycompany.com/v1beta1',
            'kind': 'Application',
        },
        expected_app_resource,
        {
            'apiVersion': 'batch/v1',
            'kind': 'Job',
        },
    ]
    self.assertEqual(expected_app_resource,
                     find_application_resource(resources))

  def test_find_application_resource_none_exists(self):
    resources = [
        {
            'apiVersion': 'v1',
            'kind': 'ServiceAccount',
        },
        {
            'apiVersion': 'application.mycompany.com/v1beta1',
            'kind': 'Application',
        },
        {
            'apiVersion': 'batch/v1',
            'kind': 'Job',
        },
    ]
    self.assertRaisesRegex(Exception, r'.*does not include an Application.*',
                           lambda: find_application_resource(resources))

  def test_find_application_resource_multiple_ones_exist(self):
    resources = [
        {
            'apiVersion': 'app.k8s.io/v1alpha1',
            'kind': 'Application',
        },
        {
            'apiVersion': 'app.k8s.io/v1beta1',
            'kind': 'Application',
        },
    ]
    self.assertRaisesRegex(Exception, r'.*multiple Applications.*',
                           lambda: find_application_resource(resources))
