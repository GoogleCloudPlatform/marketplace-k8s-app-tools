# Verification system

Apps are executed in our Verification system to ensure that:

1. Installation succeeds: All resources are applied and waited for to become healthy.
1. Functionality tests pass: The deployer starts the Tester Pod and watches its exit status. Zero means
success, non-zero means failure.
1. Uninstallation succeeds: App and all of its resources are successfully removed from the cluster.

Successful results are required before an app can be published to the Google Cloud Marketplace.

## Functionality tests

Packaging functionality tests involves the following steps:

### 1. Create a `/data-test` folder

The structure is similar to the one in `/data` folder, but with the configuration and manifests that
are only meant to be applied when the app is installed in verification mode. Following are some
examples of `/data-test` for different deployers:

* Helm-based deployer:

    ```
    data-test/
      chart/
        nginx.tar.gz
      schema.yaml
    ```

* Kubectl-based deployer:

    ```
    data-test/
      manifest/
        tester.yaml.template
      schema.yaml
    ```

### 2. Writing the test schema.yaml

The `/data-test/schema.yaml` file should be used to:

* Declare properties needed for tests, which are not already declared in `/data/schema.yaml`. One
common example is the image for the Tester Pod.
* Declare default values for the properties in `/data/schema.yaml` that do not include default values.
The Verification system will use the default values to run the app. Refer to [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md#smoke-test-an-application)
for more details.

### 3. Include a Pod manifest to execute the tests

The deployer starts the Tester Pod after all of the Kubernetes resources are healthy. It should run all
tests that assert the functionality of the app. If all tests pass, the Tester Pod must complete
with a zero exit status. Otherwise, it must complete with a non-zero exit status.

The Tester Pod needs to be annotated with `marketplace.cloud.google.com/verification:test`, so that
Verification can detect which Pod to watch for test results.

Helm-based deployers can alternatively use `helm.sh/hook:test-success`, to keep compatibility with
existing Helm tests. Our tools will replace the Helm annotation with the Verification annotation at
the time of deployment.

### 4. (Optional) Add or modify resources as needed

The `/data-test` folder is a way of including additional Kubernetes resources for verification purposes,
or even modifying existing ones. The configuration defined in `/data-test` overrides the default configuration
in `/data`, according to the following rules:

+  Helm `values.yaml` files are merged. Values defined in `/data-test`
   override the values in `/data`.
+  Schema properties are merged. Schema entries defined in `properties` from
   `/data-test/schema.yaml` will override entries defined in `properties`
   from `/data/schema.yaml`
+  All other files in `/data-test` will override files in `/data`. In case of Helm deployer, which
   contains a .tar.gz file, the files are extracted first and then replaced.

You can also refer to [examples](https://github.com/GoogleCloudPlatform/click-to-deploy/tree/master/k8s) of open source apps packaged by Google Cloud Marketplace.

## Running Verification locally

The verification triggered locally is the same as that run by our Verification system. It should be run
locally, prior to submitting the app, so that mistakes can be caught sooner. Use the [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md#smoke-test-an-application) command to run Verification:

```
mpdev verify \
  --deployer=<deployer image to be verified>
```

Make sure to include both the image name and the sha256/tag of the image; for example:

```
--deployer=gcr.io/my-project/my-app/deployer@sha256:123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
```

or

```
--deployer=gcr.io/my-project/my-app/deployer:1.0
```

Here's a summary of what happens when you run Verification:

1. The folder `/data-test` is overlayed onto `/data`, to prepare resources such as the Tester Pod.
1. A test namespace is created.
1. Manifests for the app are applied in the test namespace.
1. Statuses of Kubernetes resources are checked to ensure that the app is ready for testing.
1. Tester Pods are started. If a Tester Pod fails, the deployer Job fails.
1. The app and its resources are removed.
1. The test namespace is deleted.

## Troubleshooting verification errors

This session covers the most common errors when running `mpdev verify`.

### No value for required property: \<propertyName\>

This indicates that no value was provided for the property at installation time. Since the property is required, the installation cannot proceed. To solve this make sure that the property has a default value in either `/data/schema.yaml` or `/data-test/schema.yaml`. Example of setting a default value to a property:

```
properties:
  myProperty:
    type: string
    default: Some default value
```
