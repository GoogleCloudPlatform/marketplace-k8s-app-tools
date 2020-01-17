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

import kubectl
import unittest

TEST_BINARY = ['echo', '-n', 'kubectl']


class KubectlTest(unittest.TestCase):

  def test_create(self):
    self.assertEqual(
        kubectl.create('namespace', 'ns-1', binary=TEST_BINARY),
        'kubectl create namespace ns-1')

  def test_get(self):
    self.assertEqual(
        kubectl.get('namespaces', binary=TEST_BINARY),
        'kubectl get namespaces --output=json')

  def test_delete(self):
    self.assertEqual(
        kubectl.delete('namespace', 'ns-1', binary=TEST_BINARY),
        'kubectl delete namespace ns-1')

  def test_apply(self):
    self.assertEqual(
        kubectl.apply('/tmp/resource.yaml', binary=TEST_BINARY),
        'kubectl apply --filename=/tmp/resource.yaml')
