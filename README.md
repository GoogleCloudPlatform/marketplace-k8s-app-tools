# Overview

This repository contains a set of tools supporting the development of Kubernetes
manifests deployable via Google Cloud Marketplace. These tools will be updated
as Google Cloud Marketplace's supports additional deployment mechanisms (e.g.
[Helm](https://helm.sh)) and adopts ongoing community standard (e.g. SIG Apps defined [Application](https://github.com/kubernetes-sigs/application)).

For examples of how these tools are used, see
[marketplace-k8s-app-example](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example).

# Getting Started

## Tool dependencies

- [docker](https://docs.docker.com/install/)
- [gcloud](https://cloud.google.com/sdk/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/). You can install this tool as part of `gcloud`.
- [jq](https://github.com/stedolan/jq/wiki/Installation)
- [make](https://www.gnu.org/software/make/)

## Authorization

This guide assumes you are using a local development environment. If you need
to run these instructions from a GCE VM or use a service account identity
(e.g. for testing), see: [Advanced Authorization](#advanced-authorization)

Log in as yourself by running:

```shell
gcloud auth login
```

## Provisioning a GKE cluster and configuring kubectl to connect to it.

```
CLUSTER=cluster-1
ZONE=us-west1-a

# Create the cluster.
gcloud beta container clusters create "$CLUSTER" \
    --zone "$ZONE" \
    --machine-type "n1-standard-1" \
    --num-nodes "3"

# Configure kubectl authorization.
gcloud container clusters get-credentials "$CLUSTER" --zone "$ZONE"

# Bootstrap RBAC cluster-admin for your user.
# More info: https://cloud.google.com/kubernetes-engine/docs/how-to/role-based-access-control
kubectl create clusterrolebinding cluster-admin-binding \
  --clusterrole cluster-admin --user $(gcloud config get-value account)

# (Optional) Start up kubectl proxy.
kubectl proxy
```

## Setting up GCR

Enable the API:
https://console.cloud.google.com/apis/library/containerregistry.googleapis.com

## Updating git submodules

This repo utilizes git submodules. This repo should typically be included in your
application repo as a submodule as well. Run the following commands to make sure that
all submodules are properly populated (`git clone` does not populate submodules by
default).

```shell
git submodule sync --recursive
git submodule update --recursive --init --force
```

## Building and installing your application

Follow the examples at
[marketplace-k8s-app-example](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example).

From within your application source directory, follow these steps for a quick start:

* `make crd/install` to install the application CRD on the cluster. This needs to be
  done only once.
* `make app/install` to build all the container images and deploy the app to a target
  namespace on the cluster.
* `make app/uninstall` to delete the deployed app.

# Development guide

## Coding style

We follow [Google's coding style guides](https://google.github.io/styleguide/).

## Makefile Overview

* `app.Makefile`: Application `Makefile` should include this.
    * Application `Makefile` should define `app/build::` target to specify how to
      build application containers
    * `app.Makefile` defines 2 main targets to manage the lifecycle of the application
      on the cluster in a target namespace: `make app/install` and `make app/uninstall`.

* `crd.Makefile`: Include this to expose `make crd/install` and `make crd/uninstall`.

* `gcloud.Makefile`: Include this to conveniently derive the registry and target
  namespace from local `gcloud` and `kubectl` configurations. Without this, user has
  to define these via environment variables.

* `marketplace.Makefile`: Included as part of `app.Makefile`. Your application
  build target typically depends on one or more targets in this file. For example,
  your application might need the base `helm` deployer container to build upon.

* `ubbagent.Makefile`: Include this if your application needs to build [usage base
  metering agent](https://github.com/GoogleCloudPlatform/ubbagent).

# Appendix

## Advanced Authorization

### Running on a GCE VM

If you're running from a GCE VM, your VM must have
`https://www.googleapis.com/auth/userinfo.email` scope in order for it to
reveal the correct user name to GKE. No straight forward way to add scopes to a
VM once it's created. The easiest is to set the scope when creating the VM:

```shell
gcloud compute instances create \
  [INSTANCE_NAME] \
  --machine-type n1-standard-1 \
  --scopes cloud-platform,userinfo-email
```

To check the scopes currently granted:
```shell
curl "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=$(gcloud auth print-access-token)"
```

### Running as a service account

By default, gcloud run from GCE VMs have credentials associated with the
service account, rather than a user. We recommend configuring it to authorize
as a user (see command above) to be consistent with the Marketplace end-user
experience.

If this is not an option (e.g. integration testing), see the following:

By default, the Compute service account that the VM authorizes as does not have
k8s engine admin privilege. You need to grant that role to the service account
via the IAM Admin console.

## Defining app parameters with schema.yaml file

The `schema.yaml` file is the way to declare information that end-user needs to provide
in order to provisioning the application. For example, the name of the application, the kubernetes
namespace, service accounts, etc.

The information provided by the user for properties defined in `schema.yaml` is available at deployment time. 

If the app has dependency resources, those can also be defined in the `schema.yaml`. In case a dependency resource
does not exist, it will be provisioned on behalf of the user.

Supported resources are:
- Kubernetes service account
- Storage class

This is a simple example of a schema.yaml file:

```yaml
properties:
  name:
    type: string
    x-google-marketplace:
      type: NAME
  namespace:
    type: string
    x-google-marketplace:
      type: NAMESPACE
required:
- name
- namespace
```

Each entry is defined inside properties, and ```required``` is a list of required parameters.
We validate that all required fields are provided before starting the deployment.
In general, these parameters are saved in a ConfigMap (secrets do not show in ConfigMaps) 
and will have the same name as the keys in the schema.yaml. So in the example
above, ConfigMap would look like the following:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  ...
data:
  name: <value provided by user>
  namespace: <value provided by user>
```

Schema.yaml specification
---

### Properties

#### type

Represents the type of the input in the form for that property.

##### Supported values
- `string`
- `integer`
- `boolean`

#### title

Displayed text in the ui.

#### description

Explanation of what the property is or what is used for. Be mindful of good explanation as a way to improve user experience.

#### default

If user does not provide a value, `default` will be used.

#### minimum

The value has to be greater or equal than `minimum`.

#### maximum

The value has to be less or equal than `maximum`.

#### maxLength

The value length has to be less or equal than `maxLength`.

#### pattern

A regex pattern. The value needs to match `pattern`.

#### x-google-marketplace

This server as an annotation to tell gcp to handle that property in a special way, depending on `type`. 
It has several usages and more will be added based on demand.

#### [Examples](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example/blob/master/wordpress/schema.yaml).

---
### x-google-marketplace

#### type

It defines how this object will be handled. Each type has a different set of properties.

##### Supported values
- `NAME`: To be used as the name of the app.
- `NAMESPACE`: To be used as the kubernetes namespace where the app will installed.
- `IMAGE`: Link to a docker image.
- `REPORTING_SECRET`: The Secret resource name containing the usage reporting credentials
- `GENERATED_PASSWORD`: A value to be generated at deployment time, following common password requirements.
- `SERVICE_ACCOUNT`: A pre-provisioned kubernetes service account. If it does not exist, one is created.
- `STORAGE_CLASS`: A pre-provisioned kubernetes storage class. If it does not exist, one is created.

---

### type: GENERATED_PASSWORD

Example:

```yaml
dbPassword:
    type: string
    x-google-marketplace:
      type: GENERATED_PASSWORD
      generatedPassword:
        length: 16
```
---

### type: SERVICE_ACCOUNT

Example:

```yaml
properties:
  operatorServiceAccount:
    type: string
    x-google-marketplace:
      type: SERVICE_ACCOUNT
      serviceAccount:
        roles:
        - type: ClusterRole        # This is a cluster-wide ClusterRole
          rulesType: PREDEFINED
          rulesFromRoleName: edit  # Use predefined role named "edit"
        - type: Role               # This is a namespaced Role
          rulesType: CUSTOM        # We specify our own custom RBAC rules
          rules:
          - apiGroups: ['apps.kubernetes.io/v1alpha1']
            resources: ['Application']
            verbs: ['*']
        - type: ClusterRole
          rulesType: CUSTOM
          rules:
          - apiGroups: ['etcd.database.coreos.com/v1beta2']
            resources: ['EtcdCluster']  
            verbs: ['*']
```

---
### type: STORAGE_CLASS

```yaml
properties:
  ssdStorageClass:
    type: string
    x-google-marketplace:
      type: STORAGE_CLASS
      storageClass:
        type: SSD
```
