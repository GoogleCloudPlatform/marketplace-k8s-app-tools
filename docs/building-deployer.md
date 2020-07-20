# Building an application deployer image

This guide covers the steps to build a deployer container image for the Kubernetes
applications that you distribute on Google Cloud Marketplace.
The deployer image packages your application's configuration and runs
when users deploy your application to their clusters.

## Prerequisites

* You must be a Google Cloud Marketplace partner.
  [Read the overview of distributing Kubernetes applications on Google Cloud Marketplace](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/).

## About the deployer image

Each version of your application must contain a single **deployer image**. The
deployer image includes references to other container images that your
application uses at runtime.

The deployer image is a Docker container image that has these characteristics:

- The file system contains metadata files that define various aspects
  of deploying the application. One important purpose of the metadata is to
  is to define the UI for users who are deploying the application from the
  Google Cloud Console.

- It can be executed as a standalone
  [`Job`](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/).
  After a user enters the input parameters, the Job's Pod installs all the
  components of the application, then exits.

To install the application components, the deployer image includes the
full manifests of all Kubernetes resources that need to be installed.

## Using the `mpdev` development tools

The `mpdev` tool is a container that bundles the libraries you need to develop
and test your application. You can use it to inspect your development
environment, test your application's installation, and run smoke tests
on your application.

[Review the prerequisites, and install the development tool](tool-prerequisites.md).

For information on using `mpdev` to test your application, read the
[`mpdev` reference](mpdev-references.md).

## Building your deployer

First, decide how you want to create your Kubernetes application manifests:

- [Helm](https://helm.sh): Use Helm if you have existing charts that you want
  to import. Helm also offers a powerful templating framework, but might be
  difficult to learn.

    Learn about [building your deployer with Helm](building-deployer-helm.md).

- Simple templates with environment variables, using `envsubst`: Use this
  option if you are starting from scratch and want to get your app running
  quickly. However, the templating options with this approach are limited.

    Learn about [building your deployer with `envsubst`](building-deployer-envsubst.md).

Regardless of the method you choose, your deployer needs a `schema.yaml` file,
which declares the parameters for provisioning the app.
[Learn more about creating a schema](schema.md) for your app.

## Publishing a new version

A new app version is created by pushing the corresponding deployer image to the
staging repo and updating the Marketplace draft.

### Tagging your images

Each of your app's images **must**
[carry the primary track ID and the specific release version ID as its Docker tag](schema.md#required-published-version).
Marketplace uses the last image tagged with the same primary track ID tag when it
looks for new versions of each track.

[Learn about organizing your releases in tracks](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/set-up-environment#organize-images).

The app images are located from references in the deployer's `schema.yaml`.
Each of these images **should** carry the primary track ID as its docker tag.
It **should** also carry a unique version as its docker tag. The deployer
**should** reference these images using the unique version tag.

For example, the tags can be `1.4` (track ID) and `1.4.34` (version). The previous
deployer image carries the `1.4.33` tag, and _used_ to carry the `1.4` tag.
The app image carries both `1.4` and `1.4.34` tags. It is possible for the
app image to remain the same across minor versions, in which case it will
carry all three tags: `1.4`, `1.4.33`, and `1.4.34`.
A snapshot of the images and tags looks like this:
- deployer (new): `1.4`, `1.4.34`
- deployer (old): `1.4.33`
- app (old and new): `1.4`, `1.4.33`, `1.4.34`

### Copying of images into Marketplace public repo

NOTE: Deployer and app images in your staging repo are never visible to
Marketplace users. Users get the images from Marketplace's public Container
Registry repo.

The deployer image and all of the referenced app images will be copied
into Marketplace's public Container Registry repo. This means that
images will have new names, and potentially also new tags.

The deployer image does not, and **must not**, have the knowledge of how the
re-published images should be named or tagged. This is because at deployment
time, full names of the app images are passed to the deployer as input
parameters. This is the reason why we require that all app images used by the
deployer **must** be parameterized in `schema.yaml`.
