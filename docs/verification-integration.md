# Verification system

Applications are executed in our Verification system to ensure that:

1. Installation succeeds: All resources are applied and waited for to become healthy.
1. Functionality tests pass: The deployer starts the Tester Pod and watches its exit status. Zero means
success, non-zero means failure.
1. Uninstallation succeeds: Application and all its resources are successfully removed from the cluster.

Successful results are required before application can be published to the GCP Marketplace.

## Functionality tests

Packaging functionality tests involves the following steps.

### 1. Create a `/data-test` folder

The structure is similar to the one in `/data` folder, but with the configuration and manifests that
are only meant to be applied when the application is installed in verification mode. Some examples of
`/data-test` for different deployers:

* Helm based deployer:

    ```
    data-test/
      chart/
        nginx.tar.gz
      schema.yaml
    ```

* Kubectl based deployer:

    ```
    data-test/
      manifest/
        tester.yaml.template
      schema.yaml
    ```

### 3. Writing the test schema.yaml

The `/data-test/schema.yaml` file should be used to:

* Declare properties needed for test, which are not already declared in `/data/schema.yaml`. One 
common example is the image for the Tester Pod.
* Declare default values for the properties in `/data/schema.yaml` that do not include default values.
The Verification system will use the default values to run the application. Refer to [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md#smoke-test-an-application)
for more details.

### 4. Include a Pod manifest to execute the tests

The deployer starts the Tester Pod after all the Kubernetes resources are healthy. It should run all
tests that assert the functionality of the application. If all tests pass, the Tester Pod must complete
with a zero exit status. Otherwise, it must complete with a non-zero exit status.

The Tester Pod needs to be annotated with `marketplace.cloud.google.com/verification:test`, so the Verification
can detect which Pod to watch for test results.

Helm based deployers can alternatively use `helm.sh/hook:test-success`, to keep compatibility with
existing helm tests. Our tools will replace the helm annotation with the verification annotation during
deployment time.


### 5. (Optional) Add or modify resources as needed

The `/data-test` folder is a way of including additional Kubernetes resources for verification purposes,
or even modifying existing ones. The configuration defined in `/data-test` overrides the default configuration
in `/data` according to the following rules:

+  Helm `values.yaml` files are merged. Values defined in `/data-test`
   override the values in `/data`.
+  Schema properties are merged. Schema entries defined in `properties` from
   `/data-test/schema.yaml` will override entries defined in `properties`
   from `/data/schema.yaml`
+  All other files in `/data-test` will override files in `/data`. In case of helm deployer, which
   contains a .tar.gz file, the files are extracted first and then replaced.

You can also refer to [examples](https://github.com/GoogleCloudPlatform/click-to-deploy/tree/master/k8s) of open source apps packaged by GCP Marketplace.

## Running Verification locally

The verification triggered locally is the same run in our Verification system. It should be run prior
to submitting the application, so mistakes can be caught sooner. Use the [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md#smoke-test-an-application) command to run verification:

```
mpdev verify \
  --deployer=<deployer image to be verified>
```

Make sure to include both the image name and the sha256/tag of the image, ex:

```
--deployer=gcr.io/my-project/my-app/deployer@sha256:123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
```
or
```
--deployer=gcr.io/my-project/my-app/deployer:1.0
```

In summary, this is what happens:

1. Folder `/data-test` is overlayed on to `/data`, to prepare the resources such as the Tester Pod.
1. A test namespace is created.
1. Manifests for the app is applied in the test namespace.
1. Status on Kubernetes resources are checked to ensure that the app is ready for testing.
1. Tester Pods are started. If a Tester Pod fails, the deployer Job fails.
1. Application and its resources are removed.
1. Test namespace is deleted.
