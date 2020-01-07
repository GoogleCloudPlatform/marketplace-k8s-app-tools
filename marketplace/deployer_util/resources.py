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


def set_app_resource_ownership(app_uid, app_name, app_api_version, resource):
  """ Set the app as owner of the resource"""
  set_resource_ownership(app_uid, app_name, app_api_version, "Application",
                         resource)


def set_service_account_resource_ownership(account_uid, account_name, resource):
  """ Set the app as owner of the resource"""
  set_resource_ownership(account_uid, account_name, "v1", "ServiceAccount",
                         resource)


def set_resource_ownership(owner_uid, owner_name, owner_api_version, owner_kind,
                           resource):
  """ Set the owner of the given resource. """

  if 'metadata' not in resource:
    resource['metadata'] = {}
  if 'ownerReferences' not in resource['metadata']:
    resource['metadata']['ownerReferences'] = []

  owner_reference = None
  for existing_owner_reference in resource['metadata']['ownerReferences']:
    if existing_owner_reference['uid'] == owner_uid:
      owner_reference = existing_owner_reference
      break

  if not owner_reference:
    owner_reference = {}
    resource['metadata']['ownerReferences'].append(owner_reference)

  owner_reference['apiVersion'] = owner_api_version
  owner_reference['kind'] = owner_kind
  owner_reference['blockOwnerDeletion'] = True
  owner_reference['name'] = owner_name
  owner_reference['uid'] = owner_uid
