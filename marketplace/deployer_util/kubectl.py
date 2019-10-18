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

import logging
import subprocess

DEFAULT_BINARY = ['kubectl']


def create(resource_type, resource_name, binary=DEFAULT_BINARY):
  '''kubectl create <resource_type> <resource_name>...'''
  if not resource_type:
    raise ValueError('must define resource_type')
  if not resource_name:
    raise ValueError('must define resource_name')

  command = binary + ['create', resource_type, resource_name]

  return _run_command(command)


def get(resource, binary=DEFAULT_BINARY):
  '''kubectl get <resource> --output=json...'''
  if not resource:
    raise ValueError('must define resource')

  command = binary + ['get', resource, '--output=json']

  return _run_command(command)


def delete(resource_type, resource_name, binary=DEFAULT_BINARY):
  '''kubectl delete <resource_type> <resource_name>...'''
  if not resource_type:
    raise ValueError('must define resource_type')
  if not resource_name:
    raise ValueError('must define resource_name')

  command = binary + ['delete', resource_type, resource_name]

  return _run_command(command)


def apply(definition, binary=DEFAULT_BINARY):
  '''kubectl apply --filename=<definition>...'''
  if not definition:
    raise ValueError('must define definition')

  command = binary + ['apply', '--filename=' + definition]

  return _run_command(command)


def _run_command(command):
  '''Internal wrapper for subprocess module.'''
  logging.info('Running command: {}'.format(' '.join(command)))

  return subprocess.check_output(command).decode('utf-8')
