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

import os
import json
import yaml

from bash_util import Command
from yaml_util import load_yaml

DEPLOY_INFO_ANNOTATION = "kubernetes-engine.cloud.google.com/icon"

_PROG_HELP="""
Validates and test the deployer image.
"""

def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument('--parameters', required=True)
  parser.add_argument('--metadata', required=True)
  args = parser.parse_args()

  with open(args.metadata, "r") as metadatafile:
    metadata = json.loads(metadatafile.read())

  application = None
  for filename in os.listdir("/data"):
    resources = load_resources_yaml(filename)
    for resource in resources:
      if deep_get(resource, "kind") == "Application":
        if application is not None:
          raise Exception("More than one application defined in '/data'")
        application = resource

  if application is None:
    raise Exception("Application not found in '/data'")

  expected_partner_id = deep_get(metadata, "version", "partnerId")
  if not expected_partner_id:
    raise Exception("Metadata is misisng 'version.partnerId'")

  expected_solution_id = deep_get(metadata, "version", "solutionId")
  if not expected_solution_id:
    raise Exception("Metadata is misisng 'version.solutionId'")

  deploy_info_string = deep_get(application, "metadata", "annotations", DEPLOY_INFO_ANNOTATION)
  if not deploy_info_string:
    raise Exception("Application is missing annotation '{}'".format(DEPLOY_INFO_ANNOTATION))

  deploy_info = json.loads(deploy_info_string)

  actual_partner_id = deep_get(deploy_info, "partner_id")
  if actual_partner_id != expected_partner_id:
     match_error("Partner id in deploy info does not match metadata", expected_partner_id, actual_partner_id)

  actual_solution_id = deep_get(deploy_info, "product_id")
  if actual_solution_id != expected_solution_id:
    match_error("Product id in deploy info does not match metadata", expected_solution_id, actual_solution_id)

  images = deep_get(metadata, "version", "k8sConfig", "deployer_config_schema", "images")

  deployer_image = None
  for image in images:
    if deep_get(image, "imageType") == "DEPLOYMENT_IMAGE":
      deployer_image = deep_get(image, "imageDigest")

  schema = load_yaml("/data/schema.yaml")
  for param_name, param in schema["properties"]:

def match_error(message, expected, actual):
  raise Exception("{}. Expected: '{}'. Actual '{}'".format(message, expected, actual))

if __name__ == '__main__':
  main()