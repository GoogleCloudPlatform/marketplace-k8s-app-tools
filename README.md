# Overview

This repository contains a set of tools supporting the development of Kubernetes
manifests deployable via Google Cloud Marketplace. These tools will be updated
as Google Cloud Marketplace's supports additional deployment mechanisms (e.g.
Helm) and adopts ongoing community standard (e.g. SIG Apps defined Application).

These tools operate on the repository directory structure defined in
marketplace-k8s-app-example. By default, these tools assume that both
marketplace-k8s-app-tools and marketplace-k8s-app-example are checked out
in the same directory, but this can be configured with the `$APP_REPO`
environment variable.

# Getting Started

## Tool dependencies

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

## Authorization

Log in as yourself by running:

```shell
gcloud auth login
```

### Granting GCE VM userinfo-email scope

If you're running from a GCE VM, your VM must have
`https://www.googleapis.com/auth/userinfo.email` scope in order for it to
reveal the correct user name to GKE. No straight forward way to add scopes to a
VM once it's created. The easiest is to set the scope when creating the VM:

```shell
gcloud compute instances create \
  [INSTANCE_NAME] \
  --machine-type n1-standard-1 \
  --scopes cloud-platform,userinfo-email
```

To check the scopes currently granted:
```shell
curl "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=$(gcloud auth print-access-token)"
```

### Running as a service account

By default, gcloud run from GCE VMs have credentials associated with the
service account, rather than a user. We recommend configuring it to authorize
as a user (see command above) to be consistent with the Marketplace end-user
experience.

If this is not an option (e.g. integration testing), see the following:

#### Granting service account k8s admin privilege

By default, the Compute service account that the VM authorizes as does not have
k8s engine admin privilege. You need to grant that role to the service account
via the IAM Admin console.

## Provisioning a GKE cluster and configuring kubectl to connect to it.

```
CLUSTER_NAME=cluster-1
ZONE=us-west1-a

# Create the cluster.
gcloud beta container clusters create "$CLUSTER_NAME" \
    --zone "$ZONE" \
    --cluster-version "1.8.7-gke.1" \
    --machine-type "n1-standard-1" \
    --num-nodes "3"

# Configure kubectl authorization.
gcloud container clusters get-credentials "$CLUSTER_NAME" --zone "$ZONE"

# Bootstrap RBAC cluster-admin for your user.
# More info: https://cloud.google.com/kubernetes-engine/docs/how-to/role-based-access-control
kubectl create clusterrolebinding cluster-admin-binding \
  --clusterrole cluster-admin --user $(gcloud config get-value account)

# (Optional) Start up kubectl proxy.
kubectl proxy
```

## Setting up GCR

Enable the API:
https://console.cloud.google.com/apis/library/containerregistry.googleapis.com

## Updating git submodules

This repo utilizies git submodules. This repo should typically be included in your
application repo as a submodule as well. Run the following commands to make sure that
all submodules are properly populated. `git clone` does not populate submodules by
default.

```shell
git submodule sync --recursive
git submodule update --recursive --init --force
```

## Building and installing your application

Follow the examples at https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example

From within your application source directory, follow these steps for a quick start:

* `make crd/install` to install the application CRD on the cluster. This needs to be
  done only once.
* `make app/install` to build all the container images and deploy the app to a target
  namespace on the cluster.
* `make app/uninstall` to delete the deployed app.

# Makefile Overview

* `app.Makefile`: Application `Makefile` should include this.
    * Application `Makefile` should define `app/build::` target to specify how to
      build application containers
    * `app.Makefile` defines 2 main targets to manage the lifecycle of the application
      on the cluster in a target namespace: `make app/install` and `make app/uninstall`.

* `crd.Makefile`: Include this to expose `make crd/install` and `make crd/uninstall`.

* `gcloud.Makefile`: Include this to conveniently derive the registry and target
  namespace from local `gcloud` and `kubectl` configurations. Without this, user has
  to define these via environment variables.

* `base_containers.Makefile`: Included as part of `app.Makefile`. You application
  build target typically depends on one or more targets in this file. For example,
  your application would need the base `kubectl` deployer container to build upon.

* `ubbagent.Makefile`: Include this if your application needs to build usage base
  metering agent. See https://github.com/GoogleCloudPlatform/ubbagent

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
