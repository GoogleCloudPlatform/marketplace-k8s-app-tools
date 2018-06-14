#!/usr/bin/env python2
#
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

import hashlib
import re
from argparse import ArgumentParser

import yaml

import schema_values_common
from config_helper import Schema

_PROG_HELP = """
Reads the schemas and writes k8s manifests for objects
that need provisioning outside of the deployer to stdout.
The manifests include the deployer ConfigMap.
"""

APP_NAME_LABEL = 'application.k8s.io/name'
APP_NAMESPACE_LABEL = 'application.k8s.io/namespace'


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  manifests = process(schema, values)
  print yaml.safe_dump_all(manifests,
                           default_flow_style=False,
                           indent=2)


def process(schema, values):
  props = {}
  manifests = []
  for prop in schema.properties.values():
    if prop.service_account:
      value, sa_manifests = provision_service_account(schema, values, prop)
      props[prop.name] = value
      manifests += sa_manifests
    elif prop.storage_class:
      value, sc_manifests = provision_storage_class(schema, values, prop)
      props[prop.name] = value
      manifests += sc_manifests

  data = dict(list(values.iteritems()) + list(props.iteritems()))
  data = {k: str(v) for k, v in data.iteritems()}
  manifests.append({
      'apiVersion': 'v1',
      'kind': 'ConfigMap',
      'metadata': {
          'name': '{}-deployer-config'.format(get_name(schema, values)),
          'namespace': get_namespace(schema, values),
          'labels': {
              APP_NAME_LABEL: get_name(schema, values),
          },
      },
      'data': data,
  })
  return manifests


def provision_service_account(schema, values, prop):
  name = get_name(schema, values)
  namespace = get_namespace(schema, values)
  sa_name = dns1123_name('{}-{}'.format(name, prop.name))
  subjects = [{
      'kind': 'ServiceAccount',
      'name': sa_name,
      'namespace': namespace,
  }]
  manifests = [{
      'apiVersion': 'v1',
      'kind': 'ServiceAccount',
      'metadata': {
          'name': sa_name,
          'namespace': namespace,
          'labels': {
              APP_NAME_LABEL: name,
          },
      },
  }]
  for i, rules in prop.service_account.custom_role_rules():
    role_name = '{}:{}-r{}'.format(name, prop.name, i)
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'Role',
        'metadata': {
            'name': role_name,
            'namespace': namespace,
            'labels': {
                APP_NAME_LABEL: name,
            },
        },
        'rules': rules,
    })
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': '{}:{}-rb{}'.format(name, prop.name, i),
            'namespace': namespace,
            'labels': {
                APP_NAME_LABEL: name,
            },
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'Role',
            'name': role_name,
        },
        'subjects': subjects,
    })
  for i, rules in prop.service_account.custom_cluster_role_rules():
    role_name = '{}:{}:{}-r{}'.format(namespace, name, prop.name, i)
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRole',
        'metadata': {
            'name': role_name,
            'labels': {
                APP_NAME_LABEL: name,
                APP_NAMESPACE_LABEL: namespace,
            },
        },
        'rules': rules,
    })
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name': '{}:{}:{}-rb{}'.format(namespace, name, prop.name, i),
            'namespace': namespace,
            'labels': {
                APP_NAME_LABEL: name,
                APP_NAMESPACE_LABEL: namespace,
            },
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': role_name,
        },
        'subjects': subjects,
    })
  for role in prop.service_account.predefined_roles():
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': '{}:{}:{}-rb'.format(name, prop.name, role),
            'namespace': namespace,
            'labels': {
                APP_NAME_LABEL: name,
            },
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'Role',
            'name': role,
        },
        'subjects': subjects,
    })
  for role in prop.service_account.predefined_cluster_roles():
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name': '{}:{}:{}:{}-rb'.format(namespace, name, prop.name, role),
            'namespace': namespace,
            'labels': {
                APP_NAME_LABEL: name,
                APP_NAMESPACE_LABEL: namespace,
            },
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': role,
        },
        'subjects': subjects,
    })

  return sa_name, manifests


def get_name(schema, values):
  for prop in schema.properties.values():
    if prop.xtype == 'NAME':
      return values[prop.name]
  raise Exception(
      'Unable to find property with x-google-marketplace.type=NAME')


def get_namespace(schema, values):
  for prop in schema.properties.values():
    if prop.xtype == 'NAMESPACE':
      return values[prop.name]
  raise Exception(
      'Unable to find property with x-google-marketplace.type=NAMESPACE')


def dns1123_name(name):
  """Turns a name into a proper DNS-1123 subdomain.

  This does NOT work on all names. It assumes the name is mostly correct
  and handles only certain situations.
  """
  # Attempt to fix the input name.
  fixed = name.lower()
  fixed = re.sub(r'[^a-z0-9.-]', '', fixed)
  fixed = fixed.strip('.-')

  # Add a hash at the end if the name has been modified.
  if fixed != name or len(fixed) > 59:
    # Hash and get the first 4 characters of the hash.
    m = hashlib.sha256()
    m.update(name)
    h4sh = m.hexdigest()[:4]
    fixed = '{}-{}'.format(fixed[:59], h4sh)
  return fixed


if __name__ == '__main__':
  main()
