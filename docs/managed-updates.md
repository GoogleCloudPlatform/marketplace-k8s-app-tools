# Managed Updates (Alpha)

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
RFC 2119.

## Overview

This is a guide to integrate with Managed Updates.

Managed updates uses Kubernetes Application Lifecycle Management (KALM)
framework.

## Prerequisites

We're using a pre-release of the toolchain. Setup the following environment
variable for your shell:

```shell
export MARKETPLACE_TOOLS_TAG=0.8.0-alpha02
```

### Install mpdev

See [this doc](tool-prerequisites.md).

### GCS bucket

Create a GCS bucket to house the published version metadata. This SHOULD
be a bucket in the same project you're publishing images and SHOULD be
dedicated to this process.

```shell
gsutil mb gs://your-bucket
```

The bucket MUST allow public access. This can be done using the following
command:

```shell
gsutil iam ch allUsers:objectViewer gs://your-bucket
```

### Install KALM controller and CRDs

```shell
kubectl apply -f crd/kalm.yaml
```

### Verify your environment

Run the following to make sure everything is working.

```shell
mpdev doctor
```

### Join the whitelist

Your GCP account (i.e. emails) must be added to `managed-updates@googlegroups.com`.
Please ask our team to whitelist you.

## Releases, Tracks, Metadata

Each release of your application MUST use
[Semantic Versioning](https://semver.org).
Each release MUST have unique version.
For example: `1.0.1`, `1.0.2`, `1.3.1`, `1.3.2`.

Releases are organized into tracks. Users are expected to update to newer
releases in the same track. For example, the releases above are organized into
two separate tracks, `1.0` and `1.3`.

KALM watches for new releases in a track and make recommendations to the user.

Concretely, release version metadata YAMLs are stored in GCS. All releases under
the same track reside in the same directory. For example:
- Track directory: `gs://your-bucket/your-company/your-app/1.0`
- Release metadata YAMLs:
  - `gs://your-bucket/your-company/your-app/1.0/1.0.1.yaml`
  - `gs://your-bucket/your-company/your-app/1.0/1.0.2.yaml`

You do not have to craft these files directly. `mpdev publish` takes care of
this. See below.

Note that end users consuming your application via the public Marketplace
will pull the version metadata from the Marketplace's public GCS bucket instead
of the one you use during development, i.e. `your-bucket`.

## Image organization

Requirements about images remain the same. One addition is that images belonging
to the same release MUST be tagged with that release version, in addition to the
track.

To recap:
- Each of the image below has both `1.0` (track) and `1.0.1` (release) tags.
- There MUST be a primary application image:
  `gcr.io/your-project/your-company/your-app`. Note that the name of the primary
  image is the prefix for all other images.
- There MUST be a deployer image:
  `gcr.io/your-project/your-company/your-app/deployer`
- There MAY be other images that the application needs:
  `gcr.io/your-project/your-company/your-app/proxy`,
  `gcr.io/your-project/your-company/your-app/init`.

## Update your schema

### Top level x-google-marketplace

`schema.yaml` MUST include a top-level `x-google-marketplace` section with
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
    releaseTypes:
    - Feature
    - BugFix
    # If recommend is true, users using older releases are encouraged
    # to update as soon as possible. Useful if, for example, this release
    # fixes a critical issue.
    recommended: true

  # This MUST be specified to indicate that the deployer supports KALM.
  # Note that this could be left out or kalmSupported set to false, in
  # which case the deployer uses schema v2 but does not support update.
  managedUpdates:
    kalmSupported: true

  # Image declaration is required here. See the Images section below.
  images: {}

  # Other fields like clusterConstraints can be included here.

# properties and required sections remain the same.
```

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

Note that when end users consume your app in the public Marketplace, the final
image names will be different although they will follow the same release tag
and name prefix rule. For example, the published images could be under:
- `marketplace.gcr.io/your-company/your-app:1.0.1`
- `marketplace.gcr.io/your-company/your-app/deployer:1.0.1`
- `marketplace.gcr.io/your-company/your-app/init:1.0.1`

### Properties and Required

Properties and required sections remain largely the same.
Note that because images are now declared in the top level `x-google-marketplace`
section, there MUSTN'T be any properties with `.x-google-marketplace.type=IMAGE`.

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

This should print out the URL of the published metadata file. Its location
is deterministically derived from the GCS repo and the version.
You can now install the application at this version:

```shell
mpdev install \
  --version_meta_file=gs://your-bucket/your-company/your-app/1.0/1.0.1.yaml \
  --parameters='{"name": "installation-1", "namespace": "test"}'
```

The `--parameters` should be the same as before, which is a JSON object of
the property values.

### How the installation works

The main resources that get created by the install command:
- `Application` placholder resource. This will eventually be _updated_ by the
  deployer. Note that the resource uid would never change throughout the life
  of the installation.
- KALM `Repository` resource, which points back to the GCS bucket containing
  the version metadata files. KALM controller lists files in this bucket to
  determine which versions of the app are available.
- KALM `Release` resource, which has a reference to the actual deployer image
  that will be used to install the application. Its spec captures the version
  to be installed.
- A `Secret` which records the installation parameters.
- A `ServiceAccount` with proper permissions for running the deployer.

## Update your application

Publish a new version of your application to the same GCS directory. Let's say
the new release is `1.0.2`.

KALM controller should soon detect the availability of the new version.
In GKE UI, you should see the "new version available" notification in the
application and application list pages. You can use the UI to go through the
update process.

Alternatively, you can also update the app using CLI:

```shell
# To update to the latest available version detected by KALM.
mpdev update \
  --namespace test \
  --name installation-1

# Or to force update to a specific version
mpdev update \
  --namespace test \
  --name installation-1 \
  --version 1.0.2
```
