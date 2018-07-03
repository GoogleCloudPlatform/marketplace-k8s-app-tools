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

import collections

import google.cloud.storage

# TODO(trironkk): Test.
# TODO(trironkk): Cache clients for subsequent invocations.
# TODO(trironkk): Add support for file:/.


class InvalidPath(Exception):
  pass


def load(path):
  """Returns the contents of a path as a string."""
  bucket_name, blob_name = _parse_gs_path(path)
  client = _gcs_client()
  bucket = client.get_bucket(bucket_name)
  blob = bucket.blob(blob_name)
  return blob.download_as_string()


def _gcs_client():
  """Returns a google cloud storage client."""
  return google.cloud.storage.client.Client()


def _parse_gs_path(path):
  """Returns (bucket, blob_name) for a provided gs:/ path."""
  if not path.startswith('gs://'):
    raise InvalidPath('Invalid path: {}'.format(path))

  # Example: gs://trironkk-testing/tmp/reporting-secret.yaml
  _, _, bucket, blob_name = path.split('/', 3)

  return bucket, blob_name
