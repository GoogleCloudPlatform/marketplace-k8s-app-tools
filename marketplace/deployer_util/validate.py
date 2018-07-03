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

from argparse import ArgumentParser
from bash_util import Command
from dict_util import deep_get
from yaml_util import load_resources_yaml
from yaml_util import load_yaml

DEPLOY_INFO_ANNOTATION = "marketplace.cloud.google.com/deploy-info"
GOOGLE_MARKETPLACE = "x-google-marketplace"

_PROG_HELP="""
Validates and test the deployer image.
"""

def main():
  parser = ArgumentParser(description=_PROG_HELP)
  # parser.add_argument('--parameters', required=True)
  parser.add_argument('--metadata')
  args = parser.parse_args()

  all_resources, application = expand_and_load_resources()

  if args.metadata:
    with open(args.metadata, "r") as metadatafile:
      metadata = json.loads(metadatafile.read())
  
  if metadata:  
    validate_metadata(metadata, application)

  # images = deep_get(metadata, "version", "k8sConfig", "deployer_config_schema", "images")

  # deployer_image = None
  # for image in images:
  #   if deep_get(image, "imageType") == "DEPLOYMENT_IMAGE":
  #     deployer_image = deep_get(image, "imageDigest")

  schema = load_yaml("/data/schema.yaml")
  validate_images(schema, all_resources)


def validate_images(schema, resources):
  declared_images = [ key for key, param in schema["properties"].iteritems() 
    if deep_get(param, GOOGLE_MARKETPLACE, "type") == "IMAGE" ]

  used_images = []
  for resource in resources:
    used_images.extend(deep_find(resource, "image"))
  
  undeclared_images = [ image for image in used_images 
    if image not in declared_images ]

  if undeclared_images:
    error_message = "ERROR Images should be declared in schema file."
    print(error_message)
    for image in undeclared_images:
      print("  " + str(image))

    raise Exception(error_message)

  print("All {} used images are declared.".format(len(used_images)))

  unused_images = [ image for image in declared_images 
    if image not in used_images ]

  if unused_images:
    error_message = "ERROR Images were declared but not used."
    print(error_message)
    for image in unused_images:
      print("  " + str(image))

    raise Exception(error_message)  

  print("All {} declared images are used.".format(len(declared_images)))

  print("Images validation succeeded")


def expand_and_load_resources():
  print(Command("/bin/expand_config.py").output)
  assure_env_set('NAME', 'myapp')
  assure_env_set('NAMESPACE', 'mynamespace')
  print(Command("create_manifests.sh").output)

  application = None
  all_resources = []
  manifest_dir = "/data/manifest-expanded"
  for filename in os.listdir(manifest_dir):
    filename = os.path.join(manifest_dir, filename)
    # print_file(filename)

    Command("cat " + filename)
    resources = load_resources_yaml(filename)
    all_resources.extend(resources)
    for resource in resources:
      if deep_get(resource, "kind") == "Application":
        if application is not None:
          raise Exception("More than one application defined in '/data'")
        application = resource

  if application is None:
    raise Exception("Application not found in '/data'")

  return all_resources, application


def validate_metadata(metadata, application):
  # Validate partner id and solution id
  expected_partner_id = deep_get(metadata, "version", "partnerId")
  if not expected_partner_id:
    raise Exception("Metadata is missing 'version.partnerId'")

  expected_solution_id = deep_get(metadata, "version", "solutionId")
  if not expected_solution_id:
    raise Exception("Metadata is missing 'version.solutionId'")

  deploy_info_string = deep_get(application, "metadata", "annotations", DEPLOY_INFO_ANNOTATION)
  if not deploy_info_string:
    raise Exception("Application is missing annotation '{}'".format(DEPLOY_INFO_ANNOTATION))

  deploy_info = json.loads(deploy_info_string)

  actual_partner_id = deep_get(deploy_info, "partner_id")
  if actual_partner_id == expected_partner_id:
    print("Partner id: " + actual_partner_id)
  else:
    match_error("Partner id in deploy info does not match metadata", expected_partner_id, actual_partner_id)

  actual_solution_id = deep_get(deploy_info, "product_id")
  if actual_solution_id == expected_solution_id:
    print("Solution id: " + actual_solution_id)
  else:
    match_error("Product id in deploy info does not match metadata", expected_solution_id, actual_solution_id)

  print("Metadata validation succeeded")

def print_file(filename):
  with open(filename, "r") as stream:
    print(filename)
    print(stream.read())


def deep_find(o, key, found=[]):
  """ Finds all values with the specified key in any level of the object """
  if type(o) is dict:
    for k, value in o.iteritems():
      if k == key:
        found.append(value)
      deep_find(value, key, found)
  elif type(o) is list:
    for value in o:
      deep_find(value, key, found)

  return found


def match_error(message, expected, actual):
  raise Exception("{}. Expected: '{}'. Actual '{}'".format(message, expected, actual))


def assure_env_set(env_name, fallback_value):
  if env_name not in os.environ or not os.environ[env_name]:
    os.environ[env_name] = fallback_value


if __name__ == '__main__':
  main()