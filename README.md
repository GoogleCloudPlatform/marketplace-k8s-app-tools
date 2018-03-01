# Overview

This repository contains a set of tools supporting the development of Kubernetes
manifests deployable via Google Cloud Marketplace. These tools will be updated
as Google Cloud Marketplace's supports additional deployment mechanisms (e.g.
Helm) and adopts ongoing community standard (e.g. SIG Apps defined Application).

These tools operate on the repository directory structure defined in
marketplace-k8s-app-example. They assume the existence of two other repositories
in the same directory: marketplace-k8s-app-example and ubbagent. These repo
directories can be overridden using the `$APP_REPO` and `$AGENT_REPO`
environment variables, respectively.

# Getting Started

## Tool Dependencies

```
$ gcloud --version
Google Cloud SDK 188.0.0
alpha 2017.09.15
beta 2017.09.15
bq 2.0.28
core 2018.02.02
gsutil 4.28

$ docker --version
Docker version 17.09.0-ce, build afdb6d4

$ kubectl version
Client Version: version.Info{Major:"1", Minor:"8",
GitVersion:"v1.8.6", GitCommit:"6260bb08c46c31eea6cb538b34a9ceb3e406689c",
GitTreeState:"clean", BuildDate:"2017-12-21T06:34:11Z",
GoVersion:"go1.8.3", Compiler:"gc", Platform:"linux/amd64"} Server
Version: version.Info{Major:"1", Minor:"8+", GitVersion:"v1.8.6-gke.0",
GitCommit:"ee9a97661f14ee0b1ca31d6edd30480c89347c79",
GitTreeState:"clean", BuildDate:"2018-01-05T03:36:42Z",
GoVersion:"go1.8.3b4", Compiler:"gc", Platform:"linux/amd64"}
```

## Clone tool and example repositories.
```
$ mkdir k8s-marketplace
$ cd k8s-marketplace
$ git clone https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools.git
$ git clone https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example.git
$ git clone https://github.com/GoogleCloudPlatform/ubbagent.git
```

## Provisioning a GKE cluster and configuring kubectl to connect to it.

Note: We do not support RBAC changes that launch by default in GKE 
clusters >= 1.8, but we need >=1.8 for ownerReference based garbage
collection of CRD resources. For now, we will disable RBAC enforcement
via `--enable-legacy-authorization`.

```
CLUSTER_NAME=cluster-1
ZONE=us-west1-a

# Create the cluster.
gcloud beta container clusters create "$CLUSTER_NAME" \
    --zone "$ZONE" \
    --cluster-version "1.8.7-gke.1" \
    --machine-type "n1-standard-1" \
    --num-nodes "3" \
    --enable-legacy-authorization

# Configure kubectl authorization.
gcloud container clusters get-credentials "$CLUSTER_NAME" --zone "$ZONE"

# (Optional) Start up kubectl proxy.
kubectl proxy
```

## Set up GCR.

Enable the API:
https://console.cloud.google.com/apis/library/containerregistry.googleapis.com

## Set up environment variables.

```
export REGISTRY=gcr.io/<your_project_id>
export APP_REPO=../marketplace-k8s-app-example

export APP_NAME=wordpress
export APP_INSTANCE_NAME=$APP_NAME-1

export NAMESPACE=default
```

Note: These scripts do not manage the lifecycle of namespaces. If a custom
namespace is specified, you'll need to create it with the following command:

```
kubectl create namespace "$NAMESPACE"
```

## Install Application custom resource definition.

Cloud Marketplace relies on a Application CustomResourceDefinition for lifecycle
operations. To install this CustomResourceDefinition, run the following command:

```
make install-crd
```

Note: Google Cloud Marketplace will converge on the SIG Apps defined Application
CustomResourceDefinition, as it matures, and these tools will be updated
accordingly.

## Running Wordpress

### Run the following command to monitor relevant kubenetes resources.

Note: Don't forget to export the same variables as above (e.g. REGISTRY,
APP_REPO, APP_NAME, APP_INSTANCE_NAME, NAMESPACE).

```
make watch
```

Note: The expected initial output is empty - we haven't created anything
yet. It should look something like this:

```
=========================================================================================
Application resources in the following namespace: "<NAMESPACE>"
$ kubectl get applications --namespace="default" --show-kind
-----------------------------------------------------------------------------------------
No resources found.


=========================================================================================
Standard resources in the following namespace: "<NAMESPACE>"
$ kubectl get all --namespace="<NAMESPACE>" --show-kind
-----------------------------------------------------------------------------------------
No resources found.


=========================================================================================
Events with the following label: app="<APP_INSTANCE_NAME>"
$ kubectl get events --namespace=<NAMESPACE> --selector=app=<APP_INSTANCE_NAME> \
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'
-----------------------------------------------------------------------------------------
TIME      NAME      REASON    MESSAGE
```

### Run the following commands to create/delete/reload an application.

Note: Don't forget to export the same variables as above (e.g. REGISTRY,
APP_NAME, APP_INSTANCE_NAME, NAMESPACE).

```
# Create an application (and build if necessary):
make up

# Delete an existing application:
make down

# Reload an application (delete and recreate, rebuilding if necessary):
make reload
```

Here's a `make watch` sample output if everyting goes well:

```
======================================================================================================
Application resources in the following namespace: "<NAMESPACE>"
$ kubectl get applications --namespace="<NAMESPACE>" --show-kind
------------------------------------------------------------------------------------------------------
NAME                       AGE
applications/wordpress-1   15m


======================================================================================================
Standard resources in the following namespace: "<NAMESPACE>"
$ kubectl get all --namespace="<NAMESPACE>" --show-kind
------------------------------------------------------------------------------------------------------
NAME                           DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deploy/<APP_INSTANCE_NAME>-mysql       1         1         1            1           15m
deploy/<APP_INSTANCE_NAME>-wordpress   1         1         1            1           15m

NAME                                  DESIRED   CURRENT   READY     AGE
rs/<APP_INSTANCE_NAME>-mysql-6fc6d87d79       1         1         1         15m
rs/<APP_INSTANCE_NAME>-wordpress-6858546889   1         1         1         15m

NAME                           DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deploy/<APP_INSTANCE_NAME>-mysql       1         1         1            1           15m
deploy/<APP_INSTANCE_NAME>-wordpress   1         1         1            1           15m

NAME                                  DESIRED   CURRENT   READY     AGE
rs/<APP_INSTANCE_NAME>-mysql-6fc6d87d79       1         1         1         15m
rs/<APP_INSTANCE_NAME>-wordpress-6858546889   1         1         1         15m

NAME                        DESIRED   SUCCESSFUL   AGE
jobs/<APP_INSTANCE_NAME>-operator   1         1            15m

NAME                                        READY     STATUS    RESTARTS   AGE
po/<APP_INSTANCE_NAME>-mysql-6fc6d87d79-4thtl       1/1       Running   0          15m
po/<APP_INSTANCE_NAME>-wordpress-6858546889-vrppr   1/1       Running   0          15m

NAME                            TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
svc/<APP_INSTANCE_NAME>-mysql-svc       ClusterIP      None           <none>           3306/TCP       15m
svc/<APP_INSTANCE_NAME>-wordpress-svc   LoadBalancer   10.63.242.23   35.227.145.235   80:32612/TCP   15m



======================================================================================================
Events with the following label: app="<APP_INSTANCE_NAME>"
$ kubectl get events --namespace=<NAMESPACE> --selector=app=<APP_INSTANCE_NAME> \
    --output=custom-columns='TIME:.firstTimestamp,NAME:.metadata.name,:.reason,:.message'
------------------------------------------------------------------------------------------------------
TIME                   NAME
2018-01-30T19:05:23Z   <APP_INSTANCE_NAME>-151733912323   Cloud Marketplace   Fetching manifest from applications/<APP_INSTANCE_NAME>...
2018-01-30T19:05:24Z   <APP_INSTANCE_NAME>-151733912424   Cloud Marketplace   Starting control loop for applications/<APP_INSTANCE_NAME>...
2018-01-30T19:05:25Z   <APP_INSTANCE_NAME>-151733912525   Cloud Marketplace   Found applications/<APP_INSTANCE_NAME> ready status to be False.
2018-01-30T19:05:26Z   <APP_INSTANCE_NAME>-151733912626   Cloud Marketplace   Found applications/<APP_INSTANCE_NAME> ready status to be True.

```

# Implementation Overview

* crd/
    * SIG Apps CRD specification.

* marketplace/
    * Marketplace owned functionality.

* marketplace/start.sh
    * Shell script that creates an Application instance and marketplace/deployer
      job.

* marketplace/stop.sh
    * Shell script that deletes an Application instance, triggering cascading
      deletes.

* marketplace/deployer/
    * Container image that expands a Kubernetes manifest with provided
      environment variables and applies it to the cluster. Partners will write
      Dockerfile specifications with a FROM laucher/deployer/ instruction and
      ADD instructions for their domain specific Kubernetes manifest template.

      Note: Marketplace may maintain various implementations of this container
      image to support multiple packaging tools.

* marketplace/controller/
    * Container image that propogates health and other information from the
      checker pod to the Application instance.

      Note: This pattern is inspired from the KEP-003 ApplicationHealthCheck
      proposal. See the following for more information:
      https://github.com/kubernetes/community/pull/1629

      Note: Once a cluster-wide Application controller gains adoption
      within the Kubernetes community, we will remove this container
      and rely on the cluster-wide Application controller. This container
      is a short term workaround.

# Future Work

* marketplace/
   * Garbage collection of $APP_INSTANCE_NAME-deployer job.
   * Complete/correct the is_healthy hueristic check.
   * Support updating Application instance with dynamic information.
