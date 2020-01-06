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

import copy
import os
import sys
import yaml
import log_util as log

from argparse import ArgumentParser
from resources import set_app_resource_ownership
from yaml_util import load_resources_yaml
from yaml_util import parse_resources_yaml

_PROG_HELP = """
Scans the manifest folder kubernetes resources and set the Application to own
the ones defined in its list of components kinds.
"""
# From `kubectl api-resources --namespaced=false` with kubectl client and
# server version of 1.13
_CLUSTER_SCOPED_KINDS = [
    "ComponentStatus",
    "Namespace",
    "Node",
    "PersistentVolume",
    "MutatingWebhookConfiguration",
    "ValidatingWebhookConfiguration",
    "CustomResourceDefinition",
    "APIService",
    "TokenReview",
    "SelfSubjectAccessReview",
    "SelfSubjectRulesReview",
    "SubjectAccessReview",
    "CertificateSigningRequest",
    "PodSecurityPolicy",
    "NodeMetrics",
    "PodSecurityPolicy",
    "ClusterRoleBinding",
    "ClusterRole",
    "PriorityClass",
    "StorageClass",
    "VolumeAttachment",
]


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  parser.add_argument(
      "--app_name", help="The name of the application instance", required=True)
  parser.add_argument(
      "--app_uid", help="The uid of the application instance", required=True)
  parser.add_argument(
      "--app_api_version",
      help="The apiVersion of the Application CRD",
      required=True)
  parser.add_argument(
      "--manifests",
      help="The folder containing the manifest templates, "
      "or - to read from stdin",
      required=True)
  parser.add_argument(
      "--dest",
      help="The output file for the resulting manifest, "
      "or - to write to stdout",
      required=True)
  parser.add_argument(
      "--noapp",
      action="store_true",
      help="Do not look for Application resource to determine "
      "what kinds to include. I.e. set owner references for "
      "all of the (namespaced) resources in the manifests")
  args = parser.parse_args()

  resources = []
  if args.manifests == "-":
    resources = parse_resources_yaml(sys.stdin.read())
  elif os.path.isfile(args.manifests):
    resources = load_resources_yaml(args.manifests)
  else:
    resources = []
    for filename in os.listdir(args.manifests):
      resources += load_resources_yaml(os.path.join(args.manifests, filename))

  if not args.noapp:
    apps = [r for r in resources if r["kind"] == "Application"]

    if len(apps) == 0:
      raise Exception("Set of resources in {:s} does not include one of "
                      "Application kind".format(args.manifests))
    if len(apps) > 1:
      raise Exception("Set of resources in {:s} includes more than one of "
                      "Application kind".format(args.manifests))

    kinds = map(lambda x: x["kind"], apps[0]["spec"].get("componentKinds", []))

    excluded_kinds = ["PersistentVolumeClaim", "Application"]
    included_kinds = [kind for kind in kinds if kind not in excluded_kinds]
  else:
    included_kinds = None

  if args.dest == "-":
    dump(
        sys.stdout,
        resources,
        included_kinds,
        app_name=args.app_name,
        app_uid=args.app_uid,
        app_api_version=args.app_api_version)
    sys.stdout.flush()
  else:
    with open(args.dest, "w") as outfile:
      dump(
          outfile,
          resources,
          included_kinds,
          app_name=args.app_name,
          app_uid=args.app_uid,
          app_api_version=args.app_api_version)


def dump(outfile, resources, included_kinds, app_name, app_uid,
         app_api_version):

  def maybe_assign_ownership(resource):
    if resource["kind"] in _CLUSTER_SCOPED_KINDS:
      # Cluster-scoped resources cannot be owned by a namespaced resource:
      # https://kubernetes.io/docs/concepts/workloads/controllers/garbage-collection/#owners-and-dependents
      log.info("Application '{:s}' does not own cluster-scoped '{:s}/{:s}'",
               app_name, resource["kind"], resource["metadata"]["name"])

    if included_kinds is None or resource["kind"] in included_kinds:
      log.info("Application '{:s}' owns '{:s}/{:s}'", app_name,
               resource["kind"], resource["metadata"]["name"])
      resource = copy.deepcopy(resource)
      set_app_resource_ownership(
          app_uid=app_uid,
          app_name=app_name,
          app_api_version=app_api_version,
          resource=resource)

    return resource

  to_be_dumped = [maybe_assign_ownership(resource) for resource in resources]
  yaml.safe_dump_all(to_be_dumped, outfile, default_flow_style=False, indent=2)


if __name__ == "__main__":
  main()
