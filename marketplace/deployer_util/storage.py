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

from __future__ import absolute_import
import collections

import google.cloud.storage

# TODO(trironkk): Test.
# TODO(trironkk): Cache clients for subsequent invocations.


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
  _, _, bucket_name, blob_name = path.split('/', 3)

  client = _gcs_client()
  bucket = client.get_bucket(bucket_name)
  blob = bucket.blob(blob_name)
  return blob.download_as_string()


def _gcs_client():
  """Returns a google cloud storage client."""
  return google.cloud.storage.client.Client()


def _file_load(path):
  """Returns a file's contents as a string."""
  _, _, file_path = path.split('/', 2)
  with open(file_path, 'r') as file_handle:
      return file_handle.read()
