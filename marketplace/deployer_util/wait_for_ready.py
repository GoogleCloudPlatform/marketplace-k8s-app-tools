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

import time
import log_util as log

from argparse import ArgumentParser
from bash_util import Command

_PROG_HELP = "Wait for the application to get ready into a ready state"


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--name')
  parser.add_argument('--namespace')
  parser.add_argument('--timeout', type=float)
  args = parser.parse_args()

  log.info("Wait {} seconds for the application '{}' to get into ready state",
           args.timeout, args.name)
  previous_healthy = False

  min_time_before_healthy = 30
  poll_interval = 4

  application = Command(
      '''
    kubectl get "applications.app.k8s.io/{}"
      --namespace="{}"
      --output=json
    '''.format(args.name, args.namespace),
      print_call=True).json()

  top_level_kinds = [
      kind['kind'] for kind in application['spec']['componentKinds']
  ]

  poll_start_time = time.time()

  while True:
    top_level_resources = []
    for kind in top_level_kinds:
      resources = Command('''
        kubectl get "{}"
        --namespace="{}"
        --selector app.kubernetes.io/name="{}"
        --output=json
        '''.format(kind, args.namespace, args.name)).json()
      top_level_resources.extend(resources['items'])

    if len(top_level_resources) == 0:
      raise Exception("ERROR no top level resources found")

    log.info("Top level resources: {}", len(top_level_resources))
    healthy = True
    for resource in top_level_resources:
      healthy = is_healthy(resource)
      if not healthy:
        break

    if previous_healthy != healthy:
      log.info(
          "Initialization: Found applications.app.k8s.io/{} ready status to be {}.",
          args.name, healthy)
      previous_healthy = healthy
      if healthy:
        log.info("Wait {} seconds to make sure app stays in healthy state.",
                 min_time_before_healthy)
        healthy_start_time = time.time()

    if healthy:
      elapsed_healthy_time = time.time() - healthy_start_time
      if elapsed_healthy_time > min_time_before_healthy:
        break

    if time.time() - poll_start_time > args.timeout:
      raise Exception(
          "ERROR Application did not get ready before timeout of {} seconds"
          .format(args.timeout))

    time.sleep(poll_interval)


def is_healthy(resource):
  if resource['kind'] == "Deployment":
    return is_deployment_ready(resource)
  if resource['kind'] == "StatefulSet":
    return is_sts_ready(resource)
  if resource['kind'] == "Pod":
    return is_pod_ready(resource)
  if resource['kind'] == "Job":
    return is_job_ready(resource)
  if resource['kind'] == "PersistentVolumeClaim":
    return is_pvc_ready(resource)
  if resource['kind'] == "Service":
    return is_service_ready(resource)
  if resource['kind'] == "Ingress":
    return is_ingress_ready(resource)

  # TODO(ruela): Handle more resource types.
  return True


def is_deployment_ready(resource):
  if total_replicas(resource) == ready_replicas(resource):
    return True

  log.info("Deployment '{}' replicas are not ready: {}/{}", name(resource),
           ready_replicas(resource), total_replicas(resource))
  return False


def is_sts_ready(resource):
  if total_replicas(resource) == ready_replicas(resource):
    return True

  log.info("StatefulSet '{}' replicas are not ready: {}/{}", name(resource),
           ready_replicas(resource), total_replicas(resource))
  return False


def is_pod_ready(resource):
  if status_condition_is_true('Ready', resource):
    return True

  log.info("Pod/{} is not ready.", name(resource))
  return False


def is_job_ready(resource):
  # Don't wait for Deployer.
  if is_deployer_job(resource):
    return True

  if status_condition_is_true('Complete', resource):
    return True

  log.info("Job/{} is not ready.", name(resource))
  return False


def is_pvc_ready(resource):
  if phase(resource) == "Bound":
    return True

  log.info("pvc/{} phase is '{}'. Expected: 'Bound'", name(resource),
           phase(resource))
  return False


def is_service_ready(resource):
  if resource['spec']['type'] != "LoadBalancer":
    return True

  if service_ip(resource):
    return True

  log.info("service/{} service ip is not ready.", name(resource))
  return False


def is_ingress_ready(resource):
  if 'ingress' in resource['status']['loadBalancer']:
    return True

  log.info("Ingress/{} is not ready.", name(resource))
  return False


def is_deployer_job(resource):
  if 'app.kubernetes.io/component' in labels(resource):
    return (labels(resource)['app.kubernetes.io/component'] ==
            'deployer.marketplace.cloud.google.com')
  return False


def name(resource):
  return resource['metadata']['name']


def labels(resource):
  return resource['metadata']['labels']


def total_replicas(resource):
  return resource['spec']['replicas']


def status_condition_is_true(condition_type, resource):
  for condition in resource.get('status', {}).get('conditions', []):
    if condition['type'] == condition_type:
      return condition['status'] == 'True'
  return False


def ready_replicas(resource):
  if not 'readyReplicas' in resource['status']:
    return 0

  return resource['status']['readyReplicas']


def service_ip(resource):
  if not 'ingress' in resource['status']['loadBalancer']:
    return ""

  return resource['status']['loadBalancer']['ingress']


def phase(resource):
  return resource['status']['phase']


if __name__ == "__main__":
  main()
