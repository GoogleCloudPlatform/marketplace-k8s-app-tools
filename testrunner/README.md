# Preprequisites

This repository uses [bazel](https://bazel.build) to build the binary and
container. It also supports [cloudbuild](https://cloud.google.com/container-builder/docs/)
to build and publish your container on GCP from source.

The repository is also compatible with `go` tool. You'll need to
install dependencies separately as they are not vendored.

# How to build locally

Build and run the binary:

  ```
  bazel run runner:main -- -logtostderr --test_spec=$PWD/examples/http.yaml
  ```

Or build and run the docker container (see
[docker bazel rules](https://github.com/bazelbuild/rules_docker)
for more details):

  ```
  # Build and load the image, but don't run it.
  bazel run runner:go_image -- --norun

  # Run the installed container, mounting the test definition
  # files as a volume.
  docker run --rm \
    -v=$PWD/examples:/examples \
    bazel/runner:go_image -logtostderr --test_spec=/examples/http.yaml
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
  rm bazel-*
  ```

Then execute the following.

  ```
  gcloud container builds submit --config cloudbuild.yaml .
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
