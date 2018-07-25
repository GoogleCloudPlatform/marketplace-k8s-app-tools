#!/usr/bin/env python
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

"""Test for yaml_util"""

import unittest
import yaml
import copy

from validate import validate_images
from validate import ValidationException

resources = []
resources.append(yaml.load("""apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: myapp-mysql
spec:
  template:
    spec:
      containers:
      - image: imageMysqlValue
        name: mysql
"""))
    
resources.append(yaml.load("""apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: myapp-wordpress
spec:
  template:
    spec:
      initContainers:
      - image: imageInitValue
        name: wordpress-init
      containers:
      - image: imageWordpressValue
        name: wordpress
"""))
    
schema = yaml.load("""application_api_version: v1beta1
properties:
  name:
    type: string
    x-google-marketplace:
      type: NAME
  namespace:
    type: string
    x-google-marketplace:
      type: NAMESPACE
  imageInit:
    type: string
    default: imageInitValue
    x-google-marketplace:
      type: IMAGE
  imageWordpress:
    type: string
    default: imageWordpressValue
    x-google-marketplace:
      type: IMAGE
  imageMysql:
    type: string
    default: imageMysqlValue
    x-google-marketplace:
      type: IMAGE
required:
- name
- namespace
- imageInit
- imageWordpress
- imageMysql
""")

class ValidateTest(unittest.TestCase):

  def test_validate_images_success(self):
    validate_images(schema, resources)

  def test_validate_images_missingschema(self):
    newschema = copy.deepcopy(schema)
    del newschema['properties']['imageMysql']
    try:
      validate_images(newschema, resources)
    except ValidationException:
      return

    raise Exception("Validation didn't catch missing image in schema")
