# Tool Prerequisites

Install [Docker](https://docs.docker.com/install/). Make sure you follow the
Linux post-install instruction to enable running docker as non-root (i.e.
without having to `sudo`). Run the following to make sure that docker is
working:

```shell
docker run hello-world
```

If you use helm, install [helm](https://github.com/helm/helm).

Pull our dev container. It contains everything necessary for developing
your application.

```shell
docker pull gcr.io/cloud-marketplace-tools/k8s/dev
```

Extract the helper script for running the dev tools. This command creates
an executable `mpdev` in your user bin directory. (Note: there isn't
already the `bin` directory in your home directory, you'll need to create
it and add it to `$PATH`, or log out and log back in for it to be
automatically added to `$PATH`.)

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

## Install Application CRD

```shell
kubectl apply -f "https://raw.githubusercontent.com/GoogleCloudPlatform/marketplace-k8s-app-tools/master/crd/app-crd.yaml"
```

## Running the `doctor` tool

Run the following to diagnose and correctly setup your environment.

```shell
mpdev /scripts/doctor
```

Save your gcloud project to an environment variable.
