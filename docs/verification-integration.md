# Verification system

Applications are executed in our Verification system to ensure that:

1. Installation succeeds: All resources are applied and waited for to become healthy.
1. Functionality tests pass: The deployer starts the Tester Pod and watches its exit status.Zero means
success, non-zero means failure.
1. Uninstallation succeeds: Application and all its resources are successfully removed from the cluster.

Successful results are required before application can be published to the GCP Marketplace.

## Functionality tests

Packaging functionality tests involves some steps.

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

### 2. Include a Pod manifest to execute the tests

The deployer starts the Tester Pod after all the Kubernetes resources are healthy. It should run all
tests that assert the functionality of the application. If all tests pass, the Tester Pod must complete
with a zero exit status. Otherwise, it must complete with a non-zero exit status.

The Tester Pod needs to be annotated, so the Verification can detect which Pod to watch for test results.
The annotation to use depends on the type of the deployer, as follows:

* Helm based deployer: `helm.sh/hook:test-success`
* Kubectl based deployer: `marketplace.cloud.google.com/verification:test`

### 3. (Optional) Add or modify resources as needed

The `/data-test` folder is a way of including additional Kubernetes resources for verification purposes,
or even modifying existing ones. The configuration defined in `/data-test` overrides the default configuration
in `/data` according to the following rules:

+  Helm `values.yaml` files are merged. Values defined in `/data-test`
   override the values in `/data`.
+  Schema properties are merged. Schema entries defined in `properties` from
   `/data-test/schema.yaml` will override entries defined in `properties`
   from `/data/schema.yaml`
+  All other files in `/data-test` will override files in `/data`.

## Running Verification locally

The verification triggered locally is the same run in our Verification system. It should be run prior
to submitting the application, so mistakes can be caught sooner. Use the [mpdev](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-reference.md)
command to run verification:

```
mpdev verify \
  --deployer="$deployer"
```

In summary, this is what happens:

1. Folder `/data-test` is overlayed on to `/data`, to prepare the resources such as the Tester Pod.
1. Manifest for the app is applied.
1. Status on Kubernetes resources are checked to ensure that the app is ready for testing.
1. Tester Pods are started. If a Tester Pod fails, the deployer Job fails.
1. Application and its resources are removed.
