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

import sys
import time

from argparse import ArgumentParser
from bash_util import Command

_PROG_HELP = "Wait for the application to get ready into a ready state"


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--name')
  parser.add_argument('--namespace')
  parser.add_argument('--timeout')
  args = parser.parse_args()

  log("INFO Wait {} seconds for the application '{}' to get into ready state"
      .format(args.timeout, args.name))
  previous_healthy = False

  min_time_before_healthy = 30
  poll_interval = 4

  application = Command(
      '''
    kubectl get "applications/{}"
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

    log("INFO top level resources: {}".format(len(top_level_resources)))
    healthy = True
    for resource in top_level_resources:
      healthy = is_healthy(resource)
      if not healthy:
        break

    if previous_healthy != healthy:
      log("INFO Initialization: Found applications/{} ready status to be {}."
          .format(args.name, healthy))
      previous_healthy = healthy
      if healthy:
        log("INFO Wait {} seconds to make sure app stays in healthy state."
            .format(min_time_before_healthy))
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


def log(msg):
  sys.stdout.write(msg + "\n")
  sys.stdout.flush()


def is_healthy(resource):
  if resource['kind'] == "Deployment":
    return is_deployment_ready(resource)
  if resource['kind'] == "PersistentVolumeClaim":
    return is_pvc_ready(resource)
  if resource['kind'] == "Service":
    return is_service_ready(resource)

  # TODO(ruela): Handle more resource types.
  return True


def is_deployment_ready(resource):
  if total_replicas(resource) == ready_replicas(resource):
    return True

  log("INFO Deployment '{}' replicas are not ready: {}/{}".format(
      name(resource), ready_replicas(resource), total_replicas(resource)))
  return False


def is_pvc_ready(resource):
  if resource['status']['phase'] == "Bound":
    return True

  log("INFO pvc/{} phase is '{}'. Expected: 'Bound'".format(
      name(resource), phase(resource)))
  return False


def is_service_ready(resource):
  if resource['spec']['type'] != "LoadBalancer":
    return True

  if service_ip(resource):
    return True

  log("INFO service/{} service ip is not ready.".format(name(resource)))
  return False


def name(resource):
  return resource['metadata']['name']


def total_replicas(resource):
  return resource['spec']['replicas']


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
