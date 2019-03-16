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
from bash_util import Command
from dict_util import deep_get

import yaml

import config_helper
import schema_values_common
import storage

_PROG_HELP = """
Reads the schemas and writes k8s manifests for objects
that need provisioning outside of the deployer to stdout.
The manifests include the deployer-related resources.
"""


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument('--deployer_image', required=True)
  parser.add_argument('--deployer_entrypoint', default=None)
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  manifests = process(
      schema,
      values,
      deployer_image=args.deployer_image,
      deployer_entrypoint=args.deployer_entrypoint)
  print(yaml.safe_dump_all(manifests, default_flow_style=False, indent=2))


def process(schema, values, deployer_image, deployer_entrypoint):
  props = {}
  manifests = []
  app_name = get_name(schema, values)
  namespace = get_namespace(schema, values)

  # Inject DEPLOYER_IMAGE property values if not already present.
  values = inject_deployer_image_properties(values, schema, deployer_image)

  # Handle provisioning of reporting secrets from storage if a URI
  # is provided.
  for key, value in values.items():
    if key not in schema.properties:
      continue
    if not schema.properties[key].reporting_secret:
      continue
    if '://' in value:
      value, storage_manifests = provision_from_storage(
          key, value, app_name=app_name, namespace=namespace)
      values[key] = value
      manifests += storage_manifests

  for prop in schema.properties.values():
    if prop.name in values:
      # The value has been explicitly specified. Skip.
      continue
    if prop.service_account:
      value, sa_manifests = provision_service_account(
          schema, prop, app_name=app_name, namespace=namespace)
      props[prop.name] = value
      manifests += sa_manifests
    elif prop.storage_class:
      value, sc_manifests = provision_storage_class(
          schema, prop, app_name=app_name, namespace=namespace)
      props[prop.name] = value
      manifests += sc_manifests
    elif prop.xtype == config_helper.XTYPE_ISTIO_ENABLED:
      props[prop.name] = is_istio_injection_enabled(namespace=namespace)
    elif prop.xtype == config_helper.XTYPE_INGRESS_AVAILABLE:
      # TODO: Really populate this value.
      props[prop.name] = True

  # Merge input and provisioned properties.
  app_params = dict(list(values.iteritems()) + list(props.iteritems()))
  app_params = {k: str(v) for k, v in app_params.iteritems()}
  manifests += provision_deployer(
      schema,
      app_name=app_name,
      namespace=namespace,
      deployer_image=deployer_image,
      deployer_entrypoint=deployer_entrypoint,
      app_params=app_params)
  return manifests


def is_istio_injection_enabled(namespace):
  """Checks the configurations in the cluster to detect whether the Istio sidecar will be 
  injected (see https://istio.io/help/ops/setup/injection/).
  Some applications use this information to deploy differently to work with Istio.
  """

  # Check the istio-system namespace
  try:
    Command("kubectl get namespace/istio-system", print_call=True)
  except:
    print("Unable to detect namespace/istio-system.")
    return False

  # Check the istio-sidecar-injector deployment.
  try:
    sidecar_injector = Command(
        "kubectl get deploy/istio-sidecar-injector -n=istio-system -o=json | jq '.status.conditions[0]'",
        print_call=True).json()
    if (sidecar_injector['status'] != 'True' or
        sidecar_injector['type'] != 'Available'):
      print("deploy/istio-sidecar-injector is not available.")
      return False
  except:
    print("Unable to detect deploy/istio-sidecar-injector.")
    return False

  # Check the namespaceSelector configuration. Detect which mode the namespaceSelector is operating in:
  # - opt-in: only namespaces with istio-injection=enabled are injected.
  # - opt-out: namespaces will be injected unless they have istio-injection:disabled
  try:
    namespace_selector = Command(
        "kubectl get mutatingwebhookconfiguration/istio-sidecar-injector -o=json | jq '.webhooks[] | .namespaceSelector'",
        print_call=True).json()
    if deep_get(namespace_selector, 'matchLabels',
                'istio-injection') == 'enabled':
      namespace_selector_mode = 'opt-in'
    else:
      match_expressions = deep_get(namespace_selector, 'matchExpressions')
      if (match_expressions and len(match_expressions) > 0 and
          deep_get(match_expressions, 'key') == 'istio-injection' and
          deep_get(match_expressions, 'operator') == 'NotIn' and
          deep_get(match_expressions, 'values')[0] == 'disabled'):
        namespace_selector_mode = 'opt-out'
    if not namespace_selector_mode:
      print("Unable to determine namespace selector mode.")
      return False
  except:
    print(
        "Unable to detect mutatingwebhookconfiguration/istio-sidecar-injector.")
    return False

  # Check the istio-injection label in the namespace
  try:
    namespace_inject_annotation = Command(
        "kubectl get namespace {}} -o=json | jq '.metadata.labels.\"istio-injection\"'"
        .format(namespace),
        print_call=True).output
  except:
    print("Unable to determine the istio-injection label for namespace {}."
          .format(namespace))
    return False

  # Check if the namespace matches the selector each mode
  if (namespace_selector_mode == 'opt-in' and
      namespace_inject_annotation == 'enabled'):
    return True
  if (namespace_selector_mode == 'opt-out' and
      namespace_inject_annotation == 'disabled'):
    return False

  # Fallback to the default policy.
  try:
    policy = Command(
        "kubectl -n istio-system get configmap istio-sidecar-injector -o jsonpath='{.data.config}' | head | grep policy:",
        print_call=True).output
    if policy == "policy: enabled":
      return True
    else:
      return False
  except:
    print("istio-sidecar-injector policy.")
    return False

  return True


def inject_deployer_image_properties(values, schema, deployer_image):
  for key in schema.properties:
    if key in values:
      continue
    if not schema.properties[key].xtype == 'DEPLOYER_IMAGE':
      continue
    values[key] = deployer_image
  return values


def provision_from_storage(key, value, app_name, namespace):
  """Provisions a resource for a property specified from storage."""
  raw_manifest = storage.load(value)

  manifest = yaml.safe_load(raw_manifest)
  if 'metadata' not in manifest:
    manifest['metadata'] = {}
  resource_name = dns1123_name("{}-{}".format(app_name, key))
  manifest['metadata']['name'] = resource_name
  manifest['metadata']['namespace'] = namespace

  return resource_name, add_preprovisioned_labels([manifest], key)


def provision_deployer(schema, app_name, namespace, deployer_image,
                       deployer_entrypoint, app_params):
  """Provisions resources to run the deployer."""
  sa_name = dns1123_name('{}-deployer-sa'.format(app_name))
  pod_spec = {
      'serviceAccountName':
          sa_name,
      'containers': [{
          'name':
              'deployer',
          'image':
              deployer_image,
          'imagePullPolicy':
              'Always',
          'volumeMounts': [{
              'name': 'config-volume',
              'mountPath': '/data/values',
          },],
      },],
      'restartPolicy':
          'Never',
      'volumes': [{
          'name': 'config-volume',
          'configMap': {
              'name': "{}-deployer-config".format(app_name),
          },
      },],
  }
  if deployer_entrypoint:
    pod_spec['containers'][0]['command'] = [deployer_entrypoint]
  labels = {
      'app.kubernetes.io/component': 'deployer.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer': 'Dependent',
  }
  job_labels = {
      'app.kubernetes.io/component': 'deployer.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer': 'Main',
  }

  return [
      {
          'apiVersion': 'v1',
          'kind': 'ServiceAccount',
          'metadata': {
              'name': sa_name,
              'namespace': namespace,
              'labels': labels,
          },
      },
      {
          'apiVersion': 'rbac.authorization.k8s.io/v1',
          'kind': 'RoleBinding',
          'metadata': {
              'name': '{}-deployer-rb'.format(app_name),
              'namespace': namespace,
              'labels': labels,
          },
          'roleRef': {
              'apiGroup': 'rbac.authorization.k8s.io',
              'kind': 'ClusterRole',
              'name': 'cluster-admin',
          },
          'subjects': [{
              'kind': 'ServiceAccount',
              'name': sa_name,
          },]
      },
      {
          'apiVersion': 'v1',
          'kind': 'ConfigMap',
          'metadata': {
              'name': '{}-deployer-config'.format(app_name),
              'namespace': namespace,
              'labels': labels,
          },
          'data': app_params,
      },
      {
          'apiVersion': 'batch/v1',
          'kind': 'Job',
          'metadata': {
              'name': "{}-deployer".format(app_name),
              'namespace': namespace,
              'labels': job_labels,
          },
          'spec': {
              'template': {
                  'metadata': {
                      'annotations': {
                          'sidecar.istio.io/inject': "false",
                      },
                  },
                  'spec': pod_spec,
              },
              'backoffLimit': 0,
          },
      },
  ]


def provision_service_account(schema, prop, app_name, namespace):
  sa_name = dns1123_name('{}-{}'.format(app_name, prop.name))
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
      },
  }]
  for i, rules in enumerate(prop.service_account.custom_role_rules()):
    role_name = '{}:{}-r{}'.format(app_name, prop.name, i)
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'Role',
        'metadata': {
            'name': role_name,
            'namespace': namespace,
        },
        'rules': rules,
    })
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': '{}:{}-rb{}'.format(app_name, prop.name, i),
            'namespace': namespace,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'Role',
            'name': role_name,
        },
        'subjects': subjects,
    })
  for i, rules in enumerate(prop.service_account.custom_cluster_role_rules()):
    role_name = '{}:{}:{}-r{}'.format(namespace, app_name, prop.name, i)
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRole',
        'metadata': {
            'name': role_name,
        },
        'rules': rules,
    })
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name': '{}:{}:{}-rb{}'.format(namespace, app_name, prop.name, i),
            'namespace': namespace,
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
            'name':
                limit_name('{}:{}:{}-rb'.format(app_name, prop.name, role), 64),
            'namespace':
                namespace,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            # Note: predefined ones are actually cluster roles.
            'kind': 'ClusterRole',
            'name': role,
        },
        'subjects': subjects,
    })
  for role in prop.service_account.predefined_cluster_roles():
    manifests.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name':
                limit_name(
                    '{}:{}:{}:{}-crb'.format(namespace, app_name, prop.name,
                                             role), 64),
            'namespace':
                namespace,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': role,
        },
        'subjects': subjects,
    })
  return sa_name, add_preprovisioned_labels(manifests, prop.name)


def provision_storage_class(schema, prop, app_name, namespace):
  if prop.storage_class.ssd:
    sc_name = dns1123_name('{}-{}-{}'.format(namespace, app_name, prop.name))
    manifests = [{
        'apiVersion': 'storage.k8s.io/v1',
        'kind': 'StorageClass',
        'metadata': {
            'name': sc_name,
        },
        # Some intelligence might go here to determine what
        # provisioner and configuration to use here and below.
        'provisioner': 'kubernetes.io/gce-pd',
        'parameters': {
            'type': 'pd-ssd',
        }
    }]
    return sc_name, add_preprovisioned_labels(manifests, prop.name)
  else:
    raise Exception('Do not know how to provision for property {}'.format(
        prop.name))


def get_name(schema, values):
  return get_property_value(schema, values, 'NAME')


def get_namespace(schema, values):
  return get_property_value(schema, values, 'NAMESPACE')


def get_property_value(schema, values, xtype):
  candidates = schema.properties_matching({
      'x-google-marketplace': {
          'type': xtype,
      },
  })
  if len(candidates) != 1:
    raise Exception('Unable to find exactly one property with '
                    'x-google-marketplace.type={}'.format(xtype))
  return values[candidates[0].name]


def dns1123_name(name):
  """Turns a name into a proper DNS-1123 subdomain.

  This does NOT work on all names. It assumes the name is mostly correct
  and handles only certain situations.
  """
  # Attempt to fix the input name.
  fixed = name.lower()
  fixed = re.sub(r'[.]', '-', fixed)
  fixed = re.sub(r'[^a-z0-9-]', '', fixed)
  fixed = fixed.strip('-')
  fixed = limit_name(fixed, 64)
  return fixed


def limit_name(name, length=127):
  result = name
  if len(result) > length:
    result = result[:length - 5]
    # Hash and get the first 4 characters of the hash.
    m = hashlib.sha256()
    m.update(name)
    h4sh = m.hexdigest()[:4]
    result = '{}-{}'.format(result, h4sh)
  return result


def add_preprovisioned_labels(manifests, prop_name):
  for r in manifests:
    labels = r['metadata'].get('labels', {})
    labels['app.kubernetes.io/component'] = (
        'auto-provisioned.marketplace.cloud.google.com')
    labels['marketplace.cloud.google.com/auto-provisioned-for-property'] = (
        prop_name)
    r['metadata']['labels'] = labels
  return manifests


if __name__ == '__main__':
  main()
