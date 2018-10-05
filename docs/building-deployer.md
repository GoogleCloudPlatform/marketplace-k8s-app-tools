# Building Application Deployer

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
RFC 2119.

## Overview

Each application version is defined by one and only one **deployer image**. It
carries references to other container images the application uses at runtime.
Other than that, it does not need any other auxiliary data and, thus is
_fully encapsulated_.

A deployer image is a docker container image that serves the following purposes:

- Its file system contains well known metadata files that define various aspects
  of deploying the application. One important aspect is to drive the deployment
  configuration UI form.
- It can be executed as a standalone `Job`. Taking in user-supplied input
  parameters, the job's pod will install all components of the application
  and exits.

In order to install the application components, the deployer image carries the
full manifests of all k8s resources that need to be installed.

## Building your deployer

Decide how to craft your application k8s manifests.

- [Helm](https://helm.sh): Ideal if you have existing charts and want to import
  them. Helm also offers a powerful templating framework; the downside is a
  higher learning curve. Follow instructions [here](building-deployer-helm.md).
- Simple templating using `envsubst` (env var substitutions): Ideal if you are
  starting from scratch and want a low learning curve to get your app running on
  k8s. The downside is that templating capabilities are very limited.
  Follow instructions [here](building-deployer-envsubst.md).

## Publishing a new version

A new application version is submitted by pushing the corresponding deployer image
to the staging repo.

### Tags

The deployer image **must** carry the primary track ID as its docker tag.
Marketplace uses the image last tagged with that primary track ID tag when it looks
for new versions of each track. The deployer image **should** also carry a unique
version as its docker tag.

The application images are located from references in the deployer's `schema.yaml`.
Each of these images **should** carry the primary track ID as its docker tag.
It **should** also carry a unique version as its docker tag. The deployer
**should** reference these images using the unique version tag.

For example, the tags can be `1.4` (track ID) and `1.4.34` (version). The previous
deployer image carries the `1.4.33` tag, and _used_ to carry the `1.4` tag.
The application image carries both `1.4` and `1.4.34` tags. It is possible for the
application image to remain the same across minor versions, in which case it will
carry all three tags: `1.4`, `1.4.33`, and `1.4.34`.
A snapshot of the images and tags looks like this:
- deployer (new): `1.4`, `1.4.34`
- deployer (old): `1.4.33`
- app (old and new): `1.4`, `1.4.33`, `1.4.34`

### Copying of images into Marketplace public repo

NOTE: Deployer and application images in the staging repo are never visible to the
end users of Marketplace. In fact, they will _not_ have access to these
staging repos. End users use the images from Marketplace's public GCR repo.

The deployer image and all of the referenced application images will be copied
into the final Marketplace's public GCR repo. This means that images will have
new names, and potentially also new tags.

The deployer does _not_, and **should not**, have the knowledge of how the
re-published images should be named or tagged. This is because at deployment time,
full names of the application images are passed to the deployer as input parameters.
This is the reason why we require that all application images used by the deployer
**must** be parameterized in `schema.yaml`.
