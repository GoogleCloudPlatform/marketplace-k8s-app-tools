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

## Run tests locally

Run unit tests:

```shell
make tests/py
```

Run integration tests:

```shell
make tests/integration
```
