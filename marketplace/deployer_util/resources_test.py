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

import resources

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

  def assertListElementsEqual(self, list1, list2):
    return self.assertEqual(sorted(list1), sorted(list2))

  def test_resource_existing_ownerref_matching_uid_updates_existing(self):
    resource = {'metadata': {'ownerReferences': [{'uid': APP_UID}]}}

    resources.set_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION,
                                     'Application', resource)
    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [APP_OWNER_REF])

  def test_resource_existing_ownerref_different_uid_adds_ownerref(self):
    resource = {'metadata': {'ownerReferences': [{'uid': OTHER_UID}]}}

    resources.set_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION,
                                     'Application', resource)
    self.assertListElementsEqual(resource['metadata']['ownerReferences'], [{
        'uid': OTHER_UID
    }, APP_OWNER_REF])

  def test_resource_no_ownerrefs_ownerref(self):
    resource = {'metadata': {'ownerReferences': []}}

    resources.set_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION,
                                     'Application', resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [APP_OWNER_REF])

  def test_app_resource_ownership(self):
    resource = {'metadata': {'ownerReferences': []}}

    resources.set_app_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION,
                                         resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [APP_OWNER_REF])

  def test_service_account_resource_ownership(self):
    resource = {'metadata': {'ownerReferences': []}}

    resources.set_service_account_resource_ownership(
        '11111111-2222-3333-4444-555555555555', 'test-sa', resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'], [{
        'apiVersion': 'v1',
        'kind': 'ServiceAccount',
        'blockOwnerDeletion': True,
        'name': 'test-sa',
        'uid': '11111111-2222-3333-4444-555555555555',
    }])
