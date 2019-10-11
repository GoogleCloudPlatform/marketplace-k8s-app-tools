# Dev container references

## Overview and setup

Our dev container `gcr.io/cloud-marketplace-tools/k8s/dev`
bundles all the libraries needed for development.

When the dev container is run, gcloud configurations and
`kubeconfig` on the host are forwarded and used for invoking
`gcloud` and `kubectl`/k8s commands. To facilitate this,
the container has a script that can be extracted and used as
directly in your local environment.

The following creates an executable `mpdev` in your user bin
directory. Note: if there isn't already the `bin` directory in
your home directory, you'll need to create it and add it to `$PATH`,
or log out and log back in for it to be automatically added to `$PATH`.

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

This command is mostly equivalent to installing the application
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
for it to turn green, run any smoke tests, and tears it down.
Make sure it runs successfully before submitting the application to marketplace.

```shell
mpdev verify \
  --deployer=<YOUR DEPLOYER IMAGE>
```

The `verify` command does not take parameters as in `install` command.
Instead, it will use the default values declared in the schema file.

If a property has no default value declared in `/data/schema.yaml`,
it has to be declared in `/data-test/schema.yaml` (with exception of `NAME` and `NAMESPACE`, which are auto-generated during verification).

For example, suppose `/data/schema.yaml` looks like the following:

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

Since `instances` does not contain a default value, one needs to be declared in `/data-test/schema.yaml`, like so:

```yaml
properties:
  instances:
    type: int
    default: 2
```

Properties in `/data-test/schema.yaml` will overlay properties in `/data/schema.yaml`. This can also be used overwrite existing default values for verification.

### Publish a release's metadata

If you want to support managed updates (beta) for your application, use the
`mpdev publish` command to publish information about the release to your
Cloud Storage bucket.

Upload your container images to your Container Registry repository. Then, run
this command to publish the information for the release:

```sh
mpdev publish \
  --deployer_image=gcr.io/your-project/your-company/your-app/deployer:[VERSION] \
  --gcs_repo=gs://your-bucket/your-company/your-app/[TRACK]

```
