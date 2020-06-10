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

from bash_util import Command


class InvalidPath(Exception):
  pass


def load(path):
  """Returns the contents of a path as a string."""
  if path.startswith('gs://'):
    return _gcs_load(path)
  if path.startswith('file://'):
    return _file_load(path)
  raise ValueError('Unknown URI: {}'.format(path))


def _gcs_load(path):
  """Returns a gcs object's contents as a string."""
  return Command("gsutil cat {}".format(path)).output


def _file_load(path):
  """Returns a file's contents as a string."""
  _, _, file_path = path.split('/', 2)
  with open(file_path, 'r', encoding='utf-8') as file_handle:
    return file_handle.read()
