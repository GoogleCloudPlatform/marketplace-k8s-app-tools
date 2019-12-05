# Managed Updates (Alpha)

## Overview

This is a guide to enable managed updates for your Kubernetes application on
GCP Marketplace.

## Prerequisites

* You must have a deployer image for your application.

    [Learn about building a deployer image](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/building-deployer.md).

* This guide uses a pre-release version of the toolchain. Setup the following environment
  variable for your shell:

    ```shell
    export MARKETPLACE_TOOLS_TAG=0.8.0-alpha04
    ```

### Install the `mpdev` development tools

For steps to install the tools, see [the `mpdev` prerequisites](tool-prerequisites.md).

### Set up a GCS bucket

Create a Google Cloud Storage (GCS) bucket, where you store the metadata for your
software version. The bucket should be in the same project that you're publishing
your container images to, and should be dedicated to this process.

Use this command to create the bucket:

```shell
gsutil mb gs://your-bucket
```

The bucket must allow public read access. Set up access with the following
command:

```shell
gsutil iam ch allUsers:objectViewer gs://your-bucket
```

### Install the Kubernetes app lifecycle management (KALM) controller and CRDs

```shell
kubectl apply -f crd/kalm.yaml
```

### Verify your environment

Run the following command to verify that the development tools are installed and
configured:

```shell
mpdev doctor
```

### Join the alpha

To join the alpha, [fill out the sign-up form](https://docs.google.com/forms/d/e/1FAIpQLSf4F7G1MpB49uQrrboIdv4y_AREiLzU3oywRplVulf_C3LWmg/viewform).

## Set up Releases, Tracks, and Metadata

Each **release** of your application MUST use
[Semantic Versioning](https://semver.org).
Each release must have unique version.
For example: `1.0.1`, `1.0.2`, `1.3.1`, `1.3.2`.

Releases are organized in **tracks**. Users are expected to update to newer
releases in the same track. For example, the releases above are organized into
two separate tracks, `1.0` and `1.3`.

Managed Updates watches for new releases in a track and makes recommendations to
the user. Updating across tracks is not currently supported, as such operations
might involve additional migration steps.

Your version metadata YAMLs are stored in your GCS bucket. All releases under
the same track must be in the same directory. For example:

- Track directory: `gs://your-bucket/your-company/your-app/1.0`
- Release metadata YAMLs:
  - `gs://your-bucket/your-company/your-app/1.0/1.0.1.yaml`
  - `gs://your-bucket/your-company/your-app/1.0/1.0.2.yaml`

You can generate these files using `mpdev publish`, described in the sections below.

Note that users deploying your application from GCP Marketplace
pull the version metadata from GCP Marketplace's public GCS bucket instead
of the bucket you use during development.

## Organizing the images

[Review the requirements for your application images](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/create-app-package).

In addition to the previous requirements, images belonging
to the same **release** must be tagged with that release version, in addition to the
**track**.

A summary of the requirements is below.

- (_NEW_) Each of your images has both `1.0` (track) and `1.0.1` (release) tags.
- There must be a deployer image:
  `gcr.io/your-project/your-company/your-app/deployer`
- Your app likely has a primary application image:
  `gcr.io/your-project/your-company/your-app`.
  Note that all other images are prefixed with this name.
- You can add other images that the application needs:
  `gcr.io/your-project/your-company/your-app/proxy`,
  `gcr.io/your-project/your-company/your-app/init`.

## Update your schema

### Top level `x-google-marketplace` section

`schema.yaml` must include a top-level `x-google-marketplace` section with
the following new fields:

```yaml
x-google-marketplace:
  # MUST be v2.
  schemaVersion: v2

  # MUST match the version of the Application custom resource object.
  # This is the same as the top level applicationApiVersion field in v1.
  applicationApiVersion: v1beta1

  # The release version is required in the schema and MUST match the
  # release tag on the the deployer.
  publishedVersion: '0.1.1'
  publishedVersionMetadata:
    releaseNote: >-
      Initial release.
    # releaseTypes list is optional.
    # "Security" should only be used if this is an important update to patch
    # an existing vulnerability, as such update will be very prominent to the user.
    releaseTypes:
    - Feature
    - BugFix
    - Security
    # If recommend is true, users using older releases are encouraged
    # to update as soon as possible. Useful if, for example, this release
    # fixes a critical issue.
    recommended: true

  # This MUST be specified to indicate that the deployer supports managed updates.
  # Note that this could be left out or kalmSupported set to false, in
  # which case the deployer uses schema v2 but does not support update.
  managedUpdates:
    kalmSupported: true

  # Image declaration is required here. See the Images section below.
  images: {}

  # Other fields like clusterConstraints can be included here.

# properties and required sections remain the same.
```

The requirements for `schema.yaml` are described in
[Deployer schema](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/schema.md).

#### Images

Images are now declared in the top level `x-google-marketplace` section
instead of in individual properties. This both makes it more explicit and
provides more flexibility on how they could be used as parameters.

```yaml
x-google-marketplace:
  publishedVersion: 1.0.1

  images:
    '':  # Primary image has no name and is required.
      properties:
        imageRepo:
          type: REPO_WITH_REGISTRY
        imageTag:
          type: TAG
    init:
      properties:
        imageInitFull:
          type: FULL
        imageInitRegistry:
          type: REGISTRY
        imageInitRepo:
          type: REPO_WITHOUT_REGISTRY
        imageInitTag:
          type: TAG
```

In the example above, the following images are declared, in addition to
the deployer:
- `gcr.io/your-project/your-company/your-app:1.0.1`
- `gcr.io/your-project/your-company/your-app/init:1.0.1`

The images can be passed as parameters/values to your template/charts
using `properties` section. The `init` image above is passed to the template
under 4 different parameteres/values. They are:
- `imageInitFull`=`gcr.io/your-project/your-company/your-app:1.0.1`
- `imageInitRegistry`=`gcr.io`
- `imageInitRepo`=`your-project/your-company/your-app`
- `imageInitTag`=`1.0.1`

The primary image above is passed under 2 different parameters/values:
- `imageRepo`=`gcr.io/your-project/your-company/your-app`
- `imageTag`=`1.0.1`

Note that when users deploy your app from GCP Marketplace, the final
image names are different, but follow the same release tag
and name prefix rule. For example, the published images could be under:

- `marketplace.gcr.io/your-company/your-app:1.0.1`
- `marketplace.gcr.io/your-company/your-app/deployer:1.0.1`
- `marketplace.gcr.io/your-company/your-app/init:1.0.1`

### Properties and Required

The `properties` and `required` sections are described in the
[deployer schema](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/schema.md).
Note that because images are now declared in the top level `x-google-marketplace`
section, there must not be any properties with `.x-google-marketplace.type=IMAGE`.

## application.yaml

The `version` field of the `Application` resource MUST match the release version.

Other than that, this resource remains largely the same.

## Install your application

After building your deployer image and application images, you can publish
the version to your GCS bucket using the following command.

```shell

mpdev publish \
  --deployer_image=gcr.io/your-project/your-company/your-app/deployer:1.0.1 \
  --gcs_repo=gs://your-bucket/your-company/your-app/1.0
```

This command prints the URL of the published metadata file. Its location
is derived from the GCS repo and the version.

You can now install the application at this version:

```shell
mpdev install \
  --version_meta_file=gs://your-bucket/your-company/your-app/1.0/1.0.1.yaml \
  --parameters='{"name": "installation-1", "namespace": "test"}'
```

The `--parameters` should be the same as before, which is a JSON object of
the property values.

### How the installation works

The main resources that get created by the install command are:

- `Application` placholder resource. This will eventually be _updated_ by the
  deployer. Note that the resource uid would never change throughout the life
  of the installation.
- A KALM `Repository` resource, which points to the GCS bucket that contains
  the version metadata files. The KALM controller lists files in this bucket to
  determine which versions of the app are available.
- A KALM `Release` resource, which has a reference to the actual deployer image
  that will be used to install the application. Its spec captures the version
  to be installed.
- A `Secret`, which records the installation parameters.
- A `ServiceAccount` with proper permissions for running the deployer.

## Update your application

Publish a new version of your application to the same GCS directory. For example,
consider that the new release is `1.0.2`.

The KALM controller should detect the availability of the new version.
In the GKE UI, you should see a "new version available" notification in the
application and application list pages. You can use the UI to go through the
update process.

Alternatively, you can update the app using CLI:

```shell
# To update to the latest available version detected by KALM.
mpdev update \
  --namespace=test \
  --name=installation-1

# Or to force update to a specific version
mpdev update \
  --namespace=test \
  --name=installation-1 \
  --version=1.0.2
```
