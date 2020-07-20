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

from yaml_util import parse_resources_yaml


class YamlUtilTest(unittest.TestCase):

  def test_single_entry(self):
    content = """---
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: $APP_INSTANCE_NAME-mysql
  labels: &MysqlDeploymentLabels
    app.kubernetes.io/name: "$APP_INSTANCE_NAME"
    app.kubernetes.io/component: wordpress-mysql
spec:
  replicas: 1
  selector:
    matchLabels: *MysqlDeploymentLabels
  template:
    metadata:
      labels: *MysqlDeploymentLabels
    spec:
      containers:
      - image: $IMAGE_MYSQL
        name: mysql
        env:
        - name: "MYSQL_ROOT_PASSWORD"
          value: "example-password"
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
          subPath: data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: $APP_INSTANCE_NAME-mysql-pvc"""

    docs = parse_resources_yaml(content)
    self.assertEqual(len(docs), 1)

    doc = docs[0]
    self.assertEqual(doc['apiVersion'], "apps/v1beta2")
    self.assertEqual(doc['kind'], "Deployment")
    self.assertEqual(doc['spec']['template']['spec']['containers'][0]['name'],
                     "mysql")

  def test_multiple_entries_in_content(self):
    content = """
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: $APP_INSTANCE_NAME-mysql-pvc
  labels:
    app.kubernetes.io/name: "$APP_INSTANCE_NAME"
    app.kubernetes.io/component: wordpress-mysql
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard
  resources:
    requests:
      storage: 5Gi
---
# this entry will be ignored. And so will the one below with no comments
---
---
apiVersion: v1
kind: Service
metadata:
  name: $APP_INSTANCE_NAME-mysql-svc
  labels:
    app.kubernetes.io/name: "$APP_INSTANCE_NAME"
    app.kubernetes.io/component: wordpress-mysql
spec:
  ports:
  - port: 3306
  selector:
    app.kubernetes.io/name: $APP_INSTANCE_NAME
    app.kubernetes.io/component: wordpress-mysql
  clusterIP: None
---
"""
    docs = parse_resources_yaml(content)
    self.assertEqual(len(docs), 2)

    self.assertEqual(docs[0]['apiVersion'], "v1")
    self.assertEqual(docs[0]['kind'], "PersistentVolumeClaim")
    self.assertEqual(docs[0]['spec']['resources']['requests']['storage'], "5Gi")

    self.assertEqual(docs[1]['apiVersion'], "v1")
    self.assertEqual(docs[1]['kind'], "Service")
    self.assertEqual(docs[1]['spec']['ports'][0]['port'], 3306)
