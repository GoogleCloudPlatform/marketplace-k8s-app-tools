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

from resources import set_app_resource_ownership, set_service_account_resource_ownership

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
ACCOUNT_NAME = 'test-sa'
ACCOUNT_UID = '11111111-2222-3333-4444-555555555555'
ACCOUNT_OWNER_REF = {
    'apiVersion': 'v1',
    'kind': 'ServiceAccount',
    'blockOwnerDeletion': True,
    'name': ACCOUNT_NAME,
    'uid': ACCOUNT_UID,
}


class ResourcesTest(unittest.TestCase):

  def assertListElementsEqual(self, list1, list2):
    return self.assertEqual(sorted(list1), sorted(list2))

  def test_resource_existing_app_ownerref_matching_uid_updates_existing(self):
    resource = {'metadata': {'ownerReferences': [{'uid': APP_UID}]}}

    set_app_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [APP_OWNER_REF])

  def test_resource_existing_app_ownerref_different_uid_adds_ownerref(self):
    resource = {'metadata': {'ownerReferences': [{'uid': OTHER_UID}]}}

    set_app_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'], [{
        'uid': OTHER_UID
    }, APP_OWNER_REF])

  def test_resource_no_ownerrefs_adds_ownerref(self):
    resource = {'metadata': {'ownerReferences': []}}

    set_app_resource_ownership(APP_UID, APP_NAME, APP_API_VERSION, resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [APP_OWNER_REF])

  def test_resource_existing_sa_ownerref_matching_uid_updates_existing(self):
    resource = {'metadata': {'ownerReferences': [{'uid': ACCOUNT_UID}]}}

    set_service_account_resource_ownership(ACCOUNT_UID, ACCOUNT_NAME, resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [ACCOUNT_OWNER_REF])

  def test_resource_existing_sa_ownerref_different_uid_adds_ownerref(self):
    resource = {'metadata': {'ownerReferences': [{'uid': OTHER_UID}]}}

    set_service_account_resource_ownership(ACCOUNT_UID, ACCOUNT_NAME, resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'], [{
        'uid': OTHER_UID
    }, ACCOUNT_OWNER_REF])

  def test_resource_no_ownerrefs_sa_ownerref(self):
    resource = {'metadata': {'ownerReferences': []}}

    set_service_account_resource_ownership(ACCOUNT_UID, ACCOUNT_NAME, resource)

    self.assertListElementsEqual(resource['metadata']['ownerReferences'],
                                 [ACCOUNT_OWNER_REF])
