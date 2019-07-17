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

import yaml

import config_helper
import log_util as log
import property_generator
import schema_values_common
import storage

_PROG_HELP = """
Reads the schemas and writes k8s manifests for objects
that need provisioning outside of the deployer to stdout.
The manifests include the deployer-related resources.
"""
_CANONICAL_IMAGE_PULL_SECRET_NAMESPACE = 'default'


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument('--deployer_image', required=True)
  parser.add_argument('--deployer_entrypoint', default=None)
  parser.add_argument('--version_repo', default=None)
  parser.add_argument('--image_pull_secret', default=None)
  parser.add_argument('--canonical_image_pull_secret', default=None)
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  manifests = process(
      schema,
      values,
      deployer_image=args.deployer_image,
      deployer_entrypoint=args.deployer_entrypoint,
      version_repo=args.version_repo,
      annotated_image_pull_secret=args.image_pull_secret,
      canonical_image_pull_secret=args.canonical_image_pull_secret)
  print(yaml.safe_dump_all(manifests, default_flow_style=False, indent=2))


def process(schema, values, deployer_image, deployer_entrypoint, version_repo,
            annotated_image_pull_secret, canonical_image_pull_secret):
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
          schema,
          prop,
          app_name=app_name,
          namespace=namespace,
          image_pull_secret=annotated_image_pull_secret,
          canonical_image_pull_secret=canonical_image_pull_secret,
          get_canonical_image_pull_secret_manifest_fn=get_canonical_image_pull_secret_manifest
      )
      props[prop.name] = value
      manifests += sa_manifests
    elif prop.storage_class:
      value, sc_manifests = provision_storage_class(
          schema, prop, app_name=app_name, namespace=namespace)
      props[prop.name] = value
      manifests += sc_manifests
    elif prop.xtype == config_helper.XTYPE_ISTIO_ENABLED:
      # TODO: Really populate this value.
      props[prop.name] = False
    elif prop.xtype == config_helper.XTYPE_INGRESS_AVAILABLE:
      # TODO(#360): Really populate this value.
      props[prop.name] = True
    elif prop.password:
      props[prop.name] = property_generator.generate_password(prop.password)
    elif prop.tls_certificate:
      props[prop.name] = property_generator.generate_tls_certificate()

  # Merge input and provisioned properties.
  app_params = dict(list(values.iteritems()) + list(props.iteritems()))

  use_kalm = False
  if (schema.is_v2() and
      schema.x_google_marketplace.managed_updates.kalm_supported):
    if version_repo:
      use_kalm = True
    else:
      log.warn('The deployer supports KALM but no --version-repo specified. '
               'Falling back to provisioning the deployer job only.')

  if use_kalm:
    manifests += provision_kalm(
        schema,
        version_repo=version_repo,
        app_name=app_name,
        namespace=namespace,
        deployer_image=deployer_image,
        annotated_image_pull_secret=annotated_image_pull_secret,
        canonical_image_pull_secret=canonical_image_pull_secret,
        get_canonical_image_pull_secret_manifest_fn=get_canonical_image_pull_secret_manifest,
        app_params=app_params)
  else:
    manifests += provision_deployer(
        schema,
        app_name=app_name,
        namespace=namespace,
        deployer_image=deployer_image,
        deployer_entrypoint=deployer_entrypoint,
        annotated_image_pull_secret=annotated_image_pull_secret,
        canonical_image_pull_secret=canonical_image_pull_secret,
        get_canonical_image_pull_secret_manifest_fn=get_canonical_image_pull_secret_manifest,
        app_params=app_params)
  return manifests


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


def provision_kalm(schema, version_repo, app_name, namespace, deployer_image,
                   app_params, annotated_image_pull_secret,
                   canonical_image_pull_secret,
                   get_canonical_image_pull_secret_manifest_fn):
  """Provisions KALM resource for installing the application."""
  if not version_repo:
    raise Exception('A valid --version_repo must be specified')

  sa_name = dns1123_name('{}-deployer-sa'.format(app_name))

  labels = {
      'app.kubernetes.io/component': 'kalm.marketplace.cloud.google.com',
  }

  secret = make_v2_config(schema, deployer_image, namespace, app_name, labels,
                          app_params)

  repo = {
      'apiVersion': 'kalm.google.com/v1alpha1',
      'kind': 'Repository',
      'metadata': {
          'name': app_name,
          'namespace': namespace,
          'labels': labels,
      },
      'spec': {
          'type': 'Deployer',
          'url': version_repo,
      },
  }

  release = {
      'apiVersion': 'kalm.google.com/v1alpha1',
      'kind': 'Release',
      'metadata': {
          'name': app_name,
          'namespace': namespace,
          'labels': labels,
      },
      'spec': {
          'repositoryRef': {
              'name': app_name,
              'namespace': namespace,
          },
          'version': schema.x_google_marketplace.published_version,
          'applicationRef': {
              'name': app_name,
          },
          'serviceAccountName': sa_name,
          'valuesSecretRef': {
              'name': secret['metadata']['name']
          }
      },
  }

  service_account = {
      'apiVersion': 'v1',
      'kind': 'ServiceAccount',
      'metadata': {
          'name': sa_name,
          'namespace': namespace,
          'labels': labels,
      },
  }
  image_pull_secrets = filter(
      None, [annotated_image_pull_secret, canonical_image_pull_secret])
  if image_pull_secrets:
    service_account['imagePullSecrets'] = list(
        map(lambda secret: {'name': secret}, image_pull_secrets))

  role_binding = {
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
  }

  manifests = [
      repo,
      release,
      role_binding,
      secret,
      service_account,
  ]
  if canonical_image_pull_secret:
    # Ensure the canonical image pull secret exists in this namespace
    manifests.append(
        get_canonical_image_pull_secret_manifest_fn(canonical_image_pull_secret,
                                                    namespace))
  return manifests


def provision_deployer(schema, app_name, namespace, deployer_image,
                       deployer_entrypoint, app_params,
                       annotated_image_pull_secret, canonical_image_pull_secret,
                       get_canonical_image_pull_secret_manifest_fn):
  """Provisions resources to run the deployer."""
  sa_name = dns1123_name('{}-deployer-sa'.format(app_name))
  labels = {
      'app.kubernetes.io/component': 'deployer.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer': 'Dependent',
  }
  job_labels = {
      'app.kubernetes.io/component': 'deployer.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer': 'Main',
  }

  if schema.is_v2():
    config = make_v2_config(schema, deployer_image, namespace, app_name, labels,
                            app_params)
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
                'mountPath': '/data/values.yaml',
                'subPath': 'values.yaml',
                'readOnly': True,
            },],
        },],
        'restartPolicy':
            'Never',
        'volumes': [{
            'name': 'config-volume',
            'secret': {
                'secretName': config['metadata']['name'],
            },
        },]
    }
  else:
    config = make_v1_config(schema, namespace, app_name, labels, app_params)
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
                'name': config['metadata']['name'],
            },
        },]
    }

  if deployer_entrypoint:
    pod_spec['containers'][0]['command'] = [deployer_entrypoint]

  service_account = {
      'apiVersion': 'v1',
      'kind': 'ServiceAccount',
      'metadata': {
          'name': sa_name,
          'namespace': namespace,
          'labels': labels,
      },
  }
  image_pull_secrets = filter(
      None, [annotated_image_pull_secret, canonical_image_pull_secret])
  if image_pull_secrets:
    service_account['imagePullSecrets'] = list(
        map(lambda secret: {'name': secret}, image_pull_secrets))

  manifests = [
      service_account,
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
      config,
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
  if canonical_image_pull_secret:
    # Ensure the canonical image pull secret exists in this namespace
    manifests.append(
        get_canonical_image_pull_secret_manifest_fn(canonical_image_pull_secret,
                                                    namespace))
  return manifests


def make_v1_config(schema, namespace, app_name, labels, app_params):
  return {
      'apiVersion': 'v1',
      'kind': 'ConfigMap',
      'metadata': {
          'name': '{}-deployer-config'.format(app_name),
          'namespace': namespace,
          'labels': labels,
      },
      'data': {k: str(v) for k, v in app_params.iteritems()},
  }


def make_v2_config(schema, deployer_image, namespace, app_name, labels,
                   app_params):
  return {
      'apiVersion': 'v1',
      'kind': 'Secret',
      'metadata': {
          'name': '{}-deployer-config'.format(app_name),
          'namespace': namespace,
          'labels': labels,
      },
      'type': 'Opaque',
      'stringData': {
          'values.yaml': make_app_params_yaml(app_params, deployer_image),
      },
  }


def make_app_params_yaml(app_params, deployer_image):
  final_app_params = {k: v for k, v in app_params.iteritems()}
  final_app_params['__image_repo_prefix__'] = deployer_image_to_repo_prefix(
      deployer_image)
  return yaml.safe_dump(final_app_params, default_flow_style=False, indent=2)


def get_canonical_image_pull_secret_manifest(canonical_image_pull_secret_name,
                                             target_namespace):
  secret_data = Command("""
    kubectl get secret "{}""
    --namespace="{}"
    --output=json
    """.format(canonical_image_pull_secret_name,
               _CANONICAL_IMAGE_PULL_SECRET_NAMESPACE)).json()
  return {
      'apiVersion': 'v1',
      'kind': 'Secret',
      'metadata': {
          'name': canonical_image_pull_secret_name,
          'namespace': target_namespace,
      },
      'data': secret_data,
  }


def provision_service_account(schema, prop, app_name, namespace,
                              annotated_image_pull_secret,
                              canonical_image_pull_secret,
                              get_canonical_image_pull_secret_manifest_fn):
  sa_name = dns1123_name('{}-{}'.format(app_name, prop.name))
  subjects = [{
      'kind': 'ServiceAccount',
      'name': sa_name,
      'namespace': namespace,
  }]
  service_account = {
      'apiVersion': 'v1',
      'kind': 'ServiceAccount',
      'metadata': {
          'name': sa_name,
          'namespace': namespace,
      },
  }

  manifests = [service_account]
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

  image_pull_secrets = filter(
      None, [annotated_image_pull_secret, canonical_image_pull_secret])
  if image_pull_secrets:
    service_account['imagePullSecrets'] = list(
        map(lambda secret: {'name': secret}, image_pull_secrets))
  if canonical_image_pull_secret:
    # Ensure the canonical image pull secret exists in this namespace
    manifests.append(
        get_canonical_image_pull_secret_manifest_fn(canonical_image_pull_secret,
                                                    namespace))

  return manifests


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


def deployer_image_to_repo_prefix(deployer_image):
  # This strips off the digest or tag at the end of the image name.
  # All following examples should result in "gcr.io/test/deployer":
  # - gcr.io/test/deployer
  # - gcr.io/test/deployer@sha256:abcdef1234567890
  # - gcr.io/test/deployer:0.0.0
  image_without_tag = deployer_image.split('@')[0].split(':')[0]
  if not image_without_tag.endswith('/deployer'):
    raise Exception(
        'Deployer image must have "/deployer" as the suffix. Got {}'.format(
            deployer_image))
  return image_without_tag[:-len('/deployer')]


if __name__ == '__main__':
  main()
