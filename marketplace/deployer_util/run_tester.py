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
from bash_util import CommandException
from dict_util import deep_get
from yaml_util import load_resources_yaml

_PROG_HELP = "Deploy and run tester pods and wait for them to finish execution"


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--namespace')
  parser.add_argument('--manifest')
  parser.add_argument('--timeout', type=int, default=300)
  args = parser.parse_args()

  Command(
      '''
      kubectl apply
      --namespace="{}"
      --filename="{}"
      '''.format(args.namespace, args.manifest),
      print_call=True)

  resources = load_resources_yaml(args.manifest)

  for resource_def in resources:
    full_name = "{}/{}".format(resource_def['kind'],
                               deep_get(resource_def, 'metadata', 'name'))

    if resource_def['kind'] != 'Pod':
      log("INFO Skip '{}'".format(full_name))
      continue

    start_time = time.time()
    poll_interval = 4
    tester_timeout = args.timeout

    while True:
      try:
        resource = Command(
            '''
          kubectl get "{}"
          --namespace="{}"
          -o=json
          '''.format(full_name, args.namespace),
            print_call=True).json()
      except CommandException as ex:
        log(str(ex))
        log("INFO retrying")
        time.sleep(poll_interval)
        continue

      result = deep_get(resource, 'status', 'phase')

      if result == "Failed":
        print_logs(full_name, args.namespace)
        raise Exception("ERROR Tester '{}' failed".format(full_name))

      if result == "Succeeded":
        print_logs(full_name, args.namespace)
        log("INFO Tester '{}' succeeded".format(full_name))
        break

      if time.time() - start_time > tester_timeout:
        print_logs(full_name, args.namespace)
        raise Exception("ERROR Tester '{}' timeout".format(full_name))

      time.sleep(poll_interval)


def print_logs(full_name, namespace):
  log(
      Command('''kubectl logs {} --namespace="{}"'''.format(
          full_name, namespace)).output)


def log(msg):
  sys.stdout.write(msg + "\n")
  sys.stdout.flush()


if __name__ == "__main__":
  main()
