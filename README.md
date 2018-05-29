# Overview

This repository contains a set of tools supporting the development of Kubernetes
manifests deployable via Google Cloud Marketplace. These tools will be updated
as Google Cloud Marketplace's supports additional deployment mechanisms (e.g.
Helm) and adopts ongoing community standard (e.g. SIG Apps defined Application).

For examples of how these tools are used, see
[marketplace-k8s-app-example](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example).

# Getting Started

## Tool dependencies

- [gcloud](https://cloud.google.com/sdk/)
- [docker](https://docs.docker.com/install/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/). You can install
  this tool as part of `gcloud`.
- [jq](https://github.com/stedolan/jq/wiki/Installation)
- [make](https://www.gnu.org/software/make/)

## Authorization

This guide assumes you are using a local development environment. If you need
run these instructions from a GCE VM or use a service account identity
(e.g. for testing), see: [Advanced Authorization](#advanced-authorization)

Log in as yourself by running:

```shell
gcloud auth login
```

## Provisioning a GKE cluster and configuring kubectl to connect to it.

```
CLUSTER=cluster-1
ZONE=us-west1-a

# Create the cluster.
gcloud beta container clusters create "$CLUSTER" \
    --zone "$ZONE" \
    --machine-type "n1-standard-1" \
    --num-nodes "3"

# Configure kubectl authorization.
gcloud container clusters get-credentials "$CLUSTER" --zone "$ZONE"

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

Follow the examples at
[marketplace-k8s-app-example](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example).

From within your application source directory, follow these steps for a quick start:

* `make crd/install` to install the application CRD on the cluster. This needs to be
  done only once.
* `make app/install` to build all the container images and deploy the app to a target
  namespace on the cluster.
* `make app/uninstall` to delete the deployed app.

# Development guide

## Coding style

We follow [Google's coding style guides](https://google.github.io/styleguide/).

## Makefile Overview

* `app.Makefile`: Application `Makefile` should include this.
    * Application `Makefile` should define `app/build::` target to specify how to
      build application containers
    * `app.Makefile` defines 2 main targets to manage the lifecycle of the application
      on the cluster in a target namespace: `make app/install` and `make app/uninstall`.

* `crd.Makefile`: Include this to expose `make crd/install` and `make crd/uninstall`.

* `gcloud.Makefile`: Include this to conveniently derive the registry and target
  namespace from local `gcloud` and `kubectl` configurations. Without this, user has
  to define these via environment variables.

* `base_containers.Makefile`: Included as part of `app.Makefile`. Your application
  build target typically depends on one or more targets in this file. For example,
  your application would need the base `kubectl` deployer container to build upon.

* `ubbagent.Makefile`: Include this if your application needs to build usage base
  metering agent. See https://github.com/GoogleCloudPlatform/ubbagent

# Appendix

## Advanced Authorization

### Running on a GCE VM

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

By default, the Compute service account that the VM authorizes as does not have
k8s engine admin privilege. You need to grant that role to the service account
via the IAM Admin console.
