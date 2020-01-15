# Overview

This repository contains a set of tools supporting the development of Kubernetes
applications deployable via
[Google Cloud Marketplace](https://console.cloud.google.com/marketplace).

# Getting Started

See the [how to build your application deployer](docs/building-deployer.md) documentation.

# References

## Examples

*   The [marketplace-k8s-app-example](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example)
    repository contains example applications.

*   The [click-to-deploy](https://github.com/GoogleCloudPlatform/click-to-deploy/tree/master/k8s)
    repository contains more examples. This is the source code backing Google Click to Deploy Kubernetes
    applications listed on Google Cloud Marketplace.

## Coding style

We follow [Google's coding style guides](https://google.github.io/styleguide/).

# Development

## Setting up

### Log in `gcloud` with a Service Account

Instead of using your personal credential to log in, it's recommended
to use a Service Account instead.

A new Service Account and proper permissions can be created using the
following commands. `PROJECT-ID` is the (non-numeric) identifier of your
GCP project. This assumes that you're already logged in with `gcloud`.

```shell
gcloud iam service-accounts create \
  marketplace-dev-robot \
  --project PROJECT-ID \
  --display-name "GCP Marketplace development robot"

gcloud projects add-iam-policy-binding PROJECT-ID \
  --member serviceAccount:marketplace-dev-robot@PROJECT-ID.iam.gserviceaccount.com \
  --role roles/editor

gcloud projects add-iam-policy-binding PROJECT-ID \
  --member serviceAccount:marketplace-dev-robot@PROJECT-ID.iam.gserviceaccount.com \
  --role roles/container.admin
```

The created Service Account email will be
`marketplace-dev-robot@PROJECT-ID.iam.gserviceaccount.com`. Note that
you can replace `marketplace-dev-robot` with another name.

Now you can switch `gcloud` to using the Service Account by creating and
downloading a one-time key, and activate it.

```shell
gcloud iam service-accounts keys create ~/marketplace-dev-robot-key.json \
  --iam-account marketplace-dev-robot@PROJECT-ID.iam.gserviceaccount.com

gcloud auth activate-service-account \
  --key-file ~/marketplace-dev-robot-key.json
```

You should keep `~/marketplace-dev-robot-key.json` credential key in a safe
location. Note that this is the __only__ copy; the generated key __cannot__
be downloaded again.

### Log in application default credentials for `kubectl`

`kubectl` connecting to GKE requires application default credentials.
Log in using the following command:

```shell
gcloud auth application-default login
```

### Running the `doctor` command

At the very least, you need to connect to a GKE cluster. Follow
[this instruction](docs/tool-prerequisites.md)
to ensure you have a properly setup environment.

## Run tests locally

Run unit tests:

```shell
make tests/py
```

Run integration tests:

```shell
make tests/integration
```

## Build deployers locally

Set deployers container tag:

```shell
export MARKETPLACE_TOOLS_TAG=local-$USER
```

Build container images:

```shell
make marketplace/build
```
