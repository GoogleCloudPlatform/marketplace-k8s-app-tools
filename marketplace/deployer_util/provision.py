#!/usr/bin/env python3
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

from argparse import ArgumentParser
from make_dns1123_name import dns1123_name, limit_name

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


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  schema_values_common.add_to_argument_parser(parser)
  parser.add_argument('--deployer_image', required=True)
  parser.add_argument('--deployer_entrypoint', default=None)
  parser.add_argument('--deployer_service_account_name', required=True)
  parser.add_argument('--version_repo', default=None)
  parser.add_argument('--image_pull_secret', default=None)
  args = parser.parse_args()

  schema = schema_values_common.load_schema(args)
  values = schema_values_common.load_values(args)
  manifests = process(
      schema,
      values,
      deployer_image=args.deployer_image,
      deployer_entrypoint=args.deployer_entrypoint,
      version_repo=args.version_repo,
      image_pull_secret=args.image_pull_secret,
      deployer_service_account_name=args.deployer_service_account_name)
  print(yaml.safe_dump_all(manifests, default_flow_style=False, indent=2))


def process(schema, values, deployer_image, deployer_entrypoint, version_repo,
            image_pull_secret, deployer_service_account_name):
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
          image_pull_secret=image_pull_secret)
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
  app_params = dict(list(values.items()) + list(props.items()))

  use_kalm = False
  if (schema.is_v2() and
      schema.x_google_marketplace.managed_updates.kalm_supported):
    if version_repo:
      use_kalm = True
      log.info('Using KALM for deployment')
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
        image_pull_secret=image_pull_secret,
        app_params=app_params,
        deployer_service_account_name=deployer_service_account_name)
  else:
    manifests += provision_deployer(
        schema,
        app_name=app_name,
        namespace=namespace,
        deployer_image=deployer_image,
        deployer_entrypoint=deployer_entrypoint,
        image_pull_secret=image_pull_secret,
        app_params=app_params,
        deployer_service_account_name=deployer_service_account_name)
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
                   app_params, deployer_service_account_name,
                   image_pull_secret):
  """Provisions KALM resource for installing the application."""
  if not version_repo:
    raise Exception('A valid --version_repo must be specified')

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
          'serviceAccountName': deployer_service_account_name,
          'valuesSecretRef': {
              'name': secret['metadata']['name']
          }
      },
  }

  service_account = {
      'apiVersion': 'v1',
      'kind': 'ServiceAccount',
      'metadata': {
          'name': deployer_service_account_name,
          'namespace': namespace,
          'labels': labels,
      },
  }
  if image_pull_secret:
    service_account['imagePullSecrets'] = [{
        'name': image_pull_secret,
    }]

  role_binding = {
      'apiVersion':
          'rbac.authorization.k8s.io/v1',
      'kind':
          'RoleBinding',
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
          'name': deployer_service_account_name,
      },]
  }

  return [
      repo,
      release,
      role_binding,
      secret,
      service_account,
  ]


def provision_deployer(schema, app_name, namespace, deployer_image,
                       deployer_entrypoint, app_params,
                       deployer_service_account_name, image_pull_secret):
  """Provisions resources to run the deployer."""
  dependents_labels = {
      'app.kubernetes.io/component': 'deployer.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer': 'Dependent',
  }
  dependents_rbac_labels = {
      'app.kubernetes.io/component':
          'deployer-rbac.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer':
          'Dependent',
  }
  job_labels = {
      'app.kubernetes.io/component': 'deployer.marketplace.cloud.google.com',
      'marketplace.cloud.google.com/deployer': 'Main',
  }
  resources_requests = {'requests': {'memory': '100Mi', 'cpu': '100m'}}

  if schema.is_v2():
    config = make_v2_config(schema, deployer_image, namespace, app_name,
                            dependents_labels, app_params)
    pod_spec = {
        'serviceAccountName':
            deployer_service_account_name,
        'containers': [{
            'name': 'deployer',
            'image': deployer_image,
            'imagePullPolicy': 'Always',
            'volumeMounts': [{
                'name': 'config-volume',
                'mountPath': '/data/values.yaml',
                'subPath': 'values.yaml',
                'readOnly': True,
            },],
            'resources': resources_requests,
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
    config = make_v1_config(schema, namespace, app_name, dependents_labels,
                            app_params)
    pod_spec = {
        'serviceAccountName':
            deployer_service_account_name,
        'containers': [{
            'name': 'deployer',
            'image': deployer_image,
            'imagePullPolicy': 'Always',
            'volumeMounts': [{
                'name': 'config-volume',
                'mountPath': '/data/values',
            },],
            'resources': resources_requests,
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
          'name': deployer_service_account_name,
          'namespace': namespace,
          'labels': dependents_labels,
      },
  }
  if image_pull_secret:
    service_account['imagePullSecrets'] = [{
        'name': image_pull_secret,
    }]

  manifests = [
      service_account,
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
  manifests += make_deployer_rolebindings(schema, namespace, app_name,
                                          dependents_rbac_labels,
                                          deployer_service_account_name)
  return manifests


def make_deployer_rolebindings(schema, namespace, app_name, labels, sa_name):
  subjects = [{
      'kind': 'ServiceAccount',
      'name': sa_name,
      'namespace': namespace,
  }]
  default_rolebinding = {
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
      'subjects': subjects,
  }

  if not schema.is_v2(
  ) or not schema.x_google_marketplace.deployer_service_account:
    return [default_rolebinding]

  roles_and_rolebindings = []
  deployer_service_account = schema.x_google_marketplace.deployer_service_account

  # Set the default rolebinding if no namespace roles are defined
  if not deployer_service_account.custom_role_rules(
  ) and not deployer_service_account.predefined_roles():
    roles_and_rolebindings.append(default_rolebinding)

  for i, rules in enumerate(deployer_service_account.custom_role_rules()):
    role_name = '{}-deployer-r{}'.format(app_name, i)
    roles_and_rolebindings.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'Role',
        'metadata': {
            'name': role_name,
            'namespace': namespace,
            'labels': labels,
        },
        'rules': rules,
    })
    roles_and_rolebindings.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': '{}-deployer-rb{}'.format(app_name, i),
            'namespace': namespace,
            'labels': labels,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'Role',
            'name': role_name,
        },
        'subjects': subjects,
    })
  for i, rules in enumerate(
      deployer_service_account.custom_cluster_role_rules()):
    role_name = '{}:{}:deployer-cr{}'.format(namespace, app_name, i)
    roles_and_rolebindings.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRole',
        'metadata': {
            'name': role_name,
            'labels': labels,
        },
        'rules': rules,
    })
    roles_and_rolebindings.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name': '{}:{}:deployer-crb{}'.format(namespace, app_name, i),
            'labels': labels,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': role_name,
        },
        'subjects': subjects,
    })
  for role in deployer_service_account.predefined_roles():
    roles_and_rolebindings.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': limit_name('{}:{}-deployer-rb'.format(app_name, role), 64),
            'namespace': namespace,
            'labels': labels,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            # Note: predefined ones are actually cluster roles.
            'kind': 'ClusterRole',
            'name': role,
        },
        'subjects': subjects,
    })
  for role in deployer_service_account.predefined_cluster_roles():
    roles_and_rolebindings.append({
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name':
                limit_name(
                    '{}:{}:{}:deployer-crb'.format(namespace, app_name, role),
                    64),
            'labels':
                labels,
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': role,
        },
        'subjects': subjects,
    })

  return roles_and_rolebindings


def make_v1_config(schema, namespace, app_name, labels, app_params):
  return {
      'apiVersion': 'v1',
      'kind': 'ConfigMap',
      'metadata': {
          'name': '{}-deployer-config'.format(app_name),
          'namespace': namespace,
          'labels': labels,
      },
      'data': {k: str(v) for k, v in app_params.items()},
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
  final_app_params = {k: v for k, v in app_params.items()}
  final_app_params['__image_repo_prefix__'] = deployer_image_to_repo_prefix(
      deployer_image)
  return yaml.safe_dump(final_app_params, default_flow_style=False, indent=2)


def provision_service_account(schema, prop, app_name, namespace,
                              image_pull_secret):
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
  if image_pull_secret:
    service_account['imagePullSecrets'] = [{
        'name': image_pull_secret,
    }]

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
