# Preprequisites

This repository uses [bazel](https://bazel.build) to build the binary and
container. It also supports [cloudbuild](https://cloud.google.com/container-builder/docs/)
to build and publish your container on GCP from source.

The repository is also compatible with `go` tool. You'll need to
install dependencies separately as they are not vendored.

# How to build locally


## Binary

Build and run the binary:

  ```
  bazel run //runner:main -- -logtostderr --test_spec=$PWD/examples/testspecs/http.yaml
  ```

## Container

To build and run the docker container:

  ```
  # Run tests
  bazel test //tests:go_default_test

  # Build binary
  bazel build //runner:main

  # Make temporary directory
  mkdir -p tmp

  # Copy the file and rename it
  cp bazel-bin/runner/main tmp/testrunner

  # Build container
  docker build --tag=testrunner --file=runner/Dockerfile tmp

  # Run the installed container, mounting the test definition
  # files as a volume.
  docker run --rm \
    -v=$PWD/examples:/examples \
    testrunner -logtostderr --test_spec=/examples/testspecs/http.yaml
  ```

# Build GCP container

Two workarounds before running the command below:

- Make all the files globally readable, or bazel on cloudbuild
  will eventually complain that files are not accessible.

  ```
  chmod a+r -R *
  ```

- Remove all bazel symlinks (eventually some `.gcloudignore`
  file will help automatically ignoring these files) to avoid
  them being uploaded to cloudbuild.

  ```
  rm -r bazel-*
  ```

Then execute the following.

  ```
  gcloud builds submit --config cloudbuild.yaml .
  ```

This publishes a `testrunner` container in your project (i.e.
whatever the default project for your `gcloud` is).

You can test by pulling the published image and run it.

  ```
  export PROJECT=$(gcloud config get-value project)

  gcloud docker -- pull gcr.io/$PROJECT/testrunner

  docker run --rm \
    -v=$PWD/examples:/examples \
    gcr.io/$PROJECT/testrunner -logtostderr --test_spec=/examples/testspecs/http.yaml
  ```
