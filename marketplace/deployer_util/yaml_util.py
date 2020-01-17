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

import copy
import yaml
import log_util as log


def load_yaml(filename):
  """ Helper function for loading a single yaml entry from file """
  with open(filename, "r", encoding='utf-8') as stream:
    content = stream.read()
    return yaml.safe_load(content)


def add_or_replace(orig, dest):
  for key in orig:
    if (type(orig[key]) is dict and key in dest and type(dest[key]) is dict):
      add_or_replace(orig[key], dest[key])
    else:
      dest[key] = copy.deepcopy(orig[key])


def overlay_yaml_file(orig, dest):
  """ Helper function for merging origin yaml file into destination yaml file

  Args:
    orig: A str, the name of the origin file.
    dest: A str, the name of the destination file."""

  y1 = load_yaml(orig)
  y2 = load_yaml(dest)

  add_or_replace(y1, y2)
  with open(dest, "w", encoding='utf-8') as out:
    yaml.dump(y2, out)


def load_resources_yaml(filename):
  """Load kubernetes resources from yaml file and parses
  into structured format.

  Args:
    filename: A str, the name of the manifest file.

  Returns:
    A list of structured kubernetes resources"""

  log.info("Reading " + filename)
  with open(filename, "r", encoding='utf-8') as stream:
    content = stream.read()
    return parse_resources_yaml(content)


def parse_resources_yaml(content):
  """Parses kubernetes resources from yaml format into structured format.

  Args:
    content: A str, the yaml content to be parsed..

  Returns:
    A list of structured kubernetes resources"""

  docs_yaml = []
  for doc_yaml in yaml.safe_load_all(content):
    if doc_yaml and 'kind' in doc_yaml:
      docs_yaml.append(doc_yaml)
  return docs_yaml
