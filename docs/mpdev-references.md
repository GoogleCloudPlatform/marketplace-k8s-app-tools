# Dev container references

## Overview and setup

Our dev container `gcr.io/cloud-marketplace-tools/k8s/dev`
bundles all the libraries needed for development.

When the dev container is run, gcloud configurations and
`kubeconfig` on the host are forwarded and used for invoking
`gcloud` and `kubectl`/k8s commands. To facilitate this,
the container has a script that can be extracted and used
directly in your local environment.

The following creates an executable `mpdev` in your user bin
directory. Note: if there isn't already a `bin` directory in
your home directory, you'll need to create it, and then either
add it to `$PATH` manually or log out and then log back in to
ensure that it is automatically added to `$PATH`.

```shell
BIN_FILE="$HOME/bin/mpdev"
docker run \
  gcr.io/cloud-marketplace-tools/k8s/dev \
  cat /scripts/dev > "$BIN_FILE"
chmod +x "$BIN_FILE"
```

Run the following to make sure that the dev tool is working:

```shell
mpdev
```

## Commands

### Diagnose your environment

The doctor tool inspects your setup and recommends potential
fixes.

```shell
mpdev doctor
```

### Install an application

This command is mostly equivalent to installing an application
from Marketplace UI.

```shell
mpdev install \
  --deployer=<YOUR DEPLOYER IMAGE> \
  --parameters=<PARAMETERS AS JSON DICTIONARY>

# For example:
mpdev install
  --deployer=gcr.io/your-company/your-solution/deployer \
  --parameters='{"name": "test-deployment", "namespace": "test-ns"}'
```

### Delete an application

You can delete an application by directly deleting the application
custom resource.

```shell
kubectl delete application <APPLICATION DEPLOYMENT NAME>
```

### Smoke test an application

This script creates a new namespace, deploys the application, waits
for it to turn green, runs any smoke tests, and tears it down.
Make sure it runs successfully before submitting the application to marketplace.

```shell
mpdev verify \
  --deployer=<YOUR DEPLOYER IMAGE>
```

The `verify` command does not take parameters as in `install` command.
Instead, it uses the default values declared in the schema file.

If a property has no default value declared in `/data/schema.yaml`,
it has to be declared in `/data-test/schema.yaml` (with exception
of `NAME` and `NAMESPACE`, which are auto-generated during verification).

For example, suppose that `/data/schema.yaml` looks like the following:

```yaml
applicationApiVersion: v1beta1
properties:
  name:
    type: string
    x-google-marketplace:
      type: NAME

  namespace:
    type: string
    x-google-marketplace:
      type: NAMESPACE

  instances:
    type: int
    title: Number of instances
```

Because `instances` does not contain a default value, a default value of
`instances` must be declared in `/data-test/schema.yaml`, like so:

```yaml
properties:
  instances:
    type: int
    default: 2
```

Properties in `/data-test/schema.yaml` will override properties in
`/data/schema.yaml`. This can also be used overwrite existing default
values for verification.

### Publish a release's metadata

If you want to support managed updates (beta) for your app, your app must
store information about itself in a Cloud Storage bucket. This Cloud Storage
bucket is created and maintained automatically for your app when it is
released through GCP Marketplace. However, to test your app during
development, you must use the `mpdev publish` command to manually publish
information about the release to your Cloud Storage bucket.

Upload your container images to your Container Registry repository. Then, run
this command to publish the information for the release:

```sh
mpdev publish \
  --deployer_image=gcr.io/your-project/your-company/your-app/deployer:[VERSION] \
  --gcs_repo=gs://your-bucket/your-company/your-app/[TRACK]

```
