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
mpdev /scripts/doctor.py
```

### Install an application

This command is mostly equivalent to installing the application
from Marketplace UI.

```shell
mpdev /scripts/install \
  --deployer=<YOUR DEPLOYER IMAGE> \
  --parameters=<PARAMETERS AS JSON DICTIONARY>

# For example:
mpdev /scripts/install
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

```shell
mpdev /scripts/install \
  --deployer=<YOUR DEPLOYER IMAGE>
```

If your app requires some additional parameters other than
name and namespace, you can supply them via `--parameters`,
similar to the install command.
