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


def set_resource_ownership(app_uid, app_name, app_api_version, resource):
  """Set the app as owner of the resource"""

  if 'metadata' not in resource:
    resource['metadata'] = {}
  if 'ownerReferences' not in resource['metadata']:
    resource['metadata']['ownerReferences'] = []

  owner_reference = None
  for existing_owner_reference in resource['metadata']['ownerReferences']:
    if existing_owner_reference['uid'] == app_uid:
      owner_reference = existing_owner_reference
      break

  if not owner_reference:
    owner_reference = {}
    resource['metadata']['ownerReferences'].append(owner_reference)

  owner_reference['apiVersion'] = app_api_version
  owner_reference['kind'] = "Application"
  owner_reference['blockOwnerDeletion'] = True
  owner_reference['name'] = app_name
  owner_reference['uid'] = app_uid


def find_application_resource(resources):
  """Finds the Application resource from a list of resource manifests."""
  apps = [
      r for r in resources if r["kind"] == "Application" and
      r["apiVersion"].startswith('app.k8s.io/')
  ]
  if len(apps) == 0:
    raise Exception("Set of resources does not include an Application")
  if len(apps) > 1:
    raise Exception("Set of resources includes multiple Applications")
  return apps[0]
