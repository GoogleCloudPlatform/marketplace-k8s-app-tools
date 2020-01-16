#!/usr/bin/env python3
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
from multiprocessing.pool import ThreadPool
import queue
import subprocess
import sys
import traceback
from argparse import ArgumentParser

_PROG_HELP = """
Diagnose the environment and print out helpful instructions to fix.
"""

Task = collections.namedtuple('Task',
                              ['name', 'function', 'prerequisites', 'args'])
Task.__new__.__defaults__ = (None,) * len(Task._fields)

# Records the outcome of the execution of a task.
TaskEvent = collections.namedtuple('TaskEvent', ['name', 'success', 'message'])
TaskEvent.__new__.__defaults__ = (None,) * len(Task._fields)


class BadPrerequisitesException(Exception):
  pass


def main():
  parser = ArgumentParser(description=_PROG_HELP)
  args = parser.parse_args()
  all_good = run(
      args=args,
      docker=check_docker,
      gcloud=check_gcloud,
      gcloud_login=(check_gcloud_login, ['gcloud']),
      gcloud_project=(check_gcloud_default_project, ['gcloud_login']),
      gsutil=(check_gsutil, ['gcloud_login']),
      kubectl=check_kubectl,
      kubectl_nodes=(check_kubectl_nodes, ['kubectl']),
      crd=(check_crd, ['kubectl_nodes']))
  if all_good:
    print('\nEverything looks good to go!!')
  else:
    sys.exit(1)


def check_docker(args):
  p = subprocess.run(['docker', 'run', '--rm', 'hello-world'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
  if p.returncode != 0:
    return TaskEvent(
        success=False,
        message='docker is not installed. See '
        'https://docs.docker.com/install/')
  return TaskEvent(success=True)


def check_gcloud(args):
  p = subprocess.run(['gcloud', 'version'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
  if p.returncode != 0:
    return TaskEvent(
        success=False,
        message='gcloud is not installed. See '
        'https://cloud.google.com/sdk/install')
  return TaskEvent(success=True)


def check_gcloud_login(args):
  p = subprocess.run(['gcloud', 'config', 'get-value', 'account'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL)
  if p.returncode == 0:
    if p.stdout:
      account = p.stdout.decode('utf-8')
      if '(unset)' not in account:
        return TaskEvent(success=True)
  return TaskEvent(
      success=False,
      message='''
You need to be logged in with gcloud. Run:

gcloud auth login
''')


def check_kubectl(args):
  p = subprocess.run(['kubectl', 'help'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
  if p.returncode != 0:
    return make_run_event(
        p=p,
        success=False,
        message='''
kubectl is not installed.

See https://kubernetes.io/docs/tasks/tools/install-kubectl/#download-as-part-of-the-google-cloud-sdk
''')
  return TaskEvent(success=True)


def check_gcloud_default_project(args):
  p = subprocess.run(['gcloud', 'config', 'get-value', 'project'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL)
  if p.returncode == 0:
    if p.stdout:
      return make_run_event(
          p=p,
          success=True,
          message='''
Your gcloud default project: {stdout}

You can set an environment variables to record the GCR URL:

  export REGISTRY=gcr.io/$(gcloud config get-value project | tr ':' '/')
''')
  return TaskEvent(
      success=True,
      message='''
You must set a default project for gcloud. This project should
house your GKE cluster. Docker images should also be
published to the GCR repo under this project, so that they can
be accessible to the GKE cluster.

Run:

  # Uncomment this to also create a new configuration.
  # gcloud config configurations create marketplace

  gcloud config set project YOUR_PROJECT
''')


def check_kubectl_nodes(args):
  p = subprocess.run(['kubectl', 'get', 'nodes'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
  if p.returncode != 0:
    return make_run_event(
        p=p,
        success=False,
        message='''
Unable to query nodes from the cluster.

If you have not created a GKE cluster, you can create one by
running the following command:

  CLUSTER=cluster-1
  ZONE=us-west1-a

  # Create the cluster.
  gcloud container clusters create "$CLUSTER" \\
      --zone "$ZONE" \\
      --machine-type "n1-standard-1" \\
      --num-nodes "3"

  # Configure kubectl authorization.
  gcloud container clusters get-credentials "$CLUSTER" --zone "$ZONE"

  # Bootstrap RBAC cluster-admin for your user.
  # More info: https://cloud.google.com/kubernetes-engine/docs/how-to/role-based-access-control
  kubectl create clusterrolebinding cluster-admin-binding \\
    --clusterrole cluster-admin --user $(gcloud config get-value account)


If your kubectl should have been setup already, here's the
output of what went wrong when querying for cluster nodes:

{stdouterr}
''')
  return TaskEvent(success=True)


def check_crd(args):
  p = subprocess.run(['kubectl', 'get', 'crd/applications.app.k8s.io'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
  if p.returncode != 0:
    return make_run_event(
        p=p,
        success=False,
        message='''
Application CRD is not installed in your cluster.

Run the following to install it:

kubectl apply -f "https://raw.githubusercontent.com/GoogleCloudPlatform/marketplace-k8s-app-tools/master/crd/app-crd.yaml"

For more details about the application CRD, see
https://github.com/kubernetes-sigs/application
''')
  return TaskEvent(success=True)


# TODO(huyhg):
# - Check connected cluster to be GKE of the project.
# - Check gcloud auth configure-docker.
# - Check RBAC cluster-admin for user.
# - Check userinfo scope for GCE VM.
#   Also, to use the Google Kubernetes Engine API from a GCE VM
#   you need to add the cloud platform scope
#   ("https://www.googleapis.com/auth/cloud-platform")
#   to your VM when it is created. Scopes can be editted
#   when the VM is stopped.
# - gcloud beta compute instances set-scopes debian-workstation --zone=us-west1-c --scopes=userinfo-email,cloud-platform
# - Check for sufficient IAM privilege (GKE admin).
# - Check GCR is enabled for the project
# - If on GCE VM and using the default Compute service account
#   make sure it has k8s engine admin role.


def check_gsutil(args):
  p = subprocess.run(['gsutil', 'ls'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
  if p.returncode != 0:
    return TaskEvent(
        success=False,
        message='Unable to list the GCS buckets. Makes sure you are authenticated via gsutil.'
    )
  return TaskEvent(success=True)


def make_run_event(p, success, message):
  stdout = (p.stdout or b'').decode('utf-8').strip()
  stderr = (p.stderr or b'').decode('utf-8').strip()
  stdouterr = '\n'.join([x for x in [stdout, stderr] if x])
  return TaskEvent(
      success=success,
      message=message.format(stdout=stdout, stderr=stderr, stdouterr=stdouterr))


def run(args, **kwargs):

  def execute_task(task, event_queue):
    try:
      event = task.function(args, **task.args)
      event_queue.put(
          TaskEvent(
              name=task.name, success=event.success, message=event.message))
    except:
      event_queue.put(
          TaskEvent(
              name=task.name,
              success=False,
              message='Unexpected exception: {}'.format(
                  traceback.format_exception(*sys.exc_info()))))

  tasks = {}
  for task_name, v in kwargs.items():
    if isinstance(v, tuple):
      # Flexibly allowing variable length tuple.
      # Tuple is the essentially Task without the name.
      v = tuple(list(v) + [None] * (len(Task._fields) - len(v) - 1))
      fn, prerequisites, extra_args = v
    else:
      fn = v
      prerequisites = None
      extra_args = None
    tasks[task_name] = Task(
        name=task_name,
        function=fn,
        prerequisites=set(prerequisites or []),
        args=extra_args or {})

  # Dry-run to ensure valid DAG.
  do_run(
      tasks, lambda task, event_queue: event_queue.put(
          TaskEvent(name=task.name, success=True)))

  with ThreadPool(5) as pool:
    return do_run(
        tasks, lambda task, event_queue: pool.apply_async(
            execute_task, args=(task, event_queue)))


def do_run(tasks, run_fn):
  dones = set()
  starteds = set()
  failed = False
  event_queue = queue.Queue()

  while True:
    if len(dones) >= len(tasks):
      break
    if failed and len(dones) >= len(starteds):
      break

    if not failed:
      # Identify tasks that have become eligible (0 prerequisites)
      # and execute them. Note that identified eligible tasks might be
      # already running and need to be filtered out. This is because we
      # handle one task event at a time.
      prereq_counts = [(task.name, len(task.prerequisites.difference(dones)))
                       for task in tasks.values()
                       if task.name not in dones]
      prereq_counts.sort(key=lambda name_count: name_count[1], reverse=True)
      candidate_names = [name for (name, count) in prereq_counts if count == 0]
      if not candidate_names:
        raise BadPrerequisitesException('Found a cycle in {}'.format(
            [name for (name, _) in prereq_counts]))
      for name in [c for c in candidate_names if c not in starteds]:
        starteds.add(name)
        run_fn(tasks[name], event_queue)

    # Wait for and process the next task event.
    task_event = event_queue.get()
    if task_event.name:
      dones.add(task_event.name)
      if not task_event.success:
        failed = True
      if task_event.message:
        print('\n{}\n\n===='.format(task_event.message.strip()))

  return not failed


if __name__ == "__main__":
  main()
