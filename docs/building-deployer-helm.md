# Building Helm Deployer

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
RFC 2119.

## Prerequisites

See [this doc](tool-prerequisites.md).

## Part 1: Up and running

The goal of this step is to build the minimal deployer to deploy your
helm chart.

In this tutorial, we use the public `wordpress` helm chart as the
example to import.

Set up a clean directory to house all of your deployer contents. This
directory is assumed to be the working directory from now on.

### Download the helm chart

```shell
helm fetch --untar --destination chart stable/wordpress
```

This will result in the following directory structure:

```text
.
└── chart
    └── wordpress
        ├── charts
        │   └── mariadb
        │       ├── Chart.yaml
        │       ├── templates
        │       │   └── ... # Template files
        │       └── values.yaml
        ├── Chart.yaml
        ├── README.md
        ├── requirements.lock
        ├── requirements.yaml
        ├── templates
        │   └── ... # Template files
        └── values.yaml
```

### Create the initial schema

Create a `schema.yaml` at the top level.

```text
.
├── schema.yaml
└── chart
    └── wordpress
        └── ... # Chart contents
```

Use the following content:

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

required:
- name
- namespace
```

### Add an application descriptor

In the main chart's `templates` directory, add `application.yaml`
with the following content. This manifest describes the application
and is used in the UI.

```yaml
apiVersion: app.k8s.io/v1beta1
kind: Application
metadata:
  name: "{{ .Release.Name }}"
  namespace: "{{ .Release.Namespace }}"
  labels:
    app.kubernetes.io/name: "{{ .Release.Name }}"
spec:
  descriptor:
    type: Wordpress
    versions: '6'
  selector:
    matchLabels:
      app.kubernetes.io/name: "{{ .Release.Name }}"
  componentKinds:
  - group: batch/v1
    kind: Job
```

### Build your deployer container

When you have the above directory structure, you can
use the `onbuild` version of container image to simplify
the process. To summarize, the directory structure is similar
to the following:

```text
.
├── chart
│   └── wordpress
│       ├── charts
│       │   └── mariadb
│       │       └── ... # subchart contents
│       ├── Chart.yaml
│       ├── README.md
│       ├── requirements.lock
│       ├── requirements.yaml
│       ├── templates
│       │   ├── application.yaml
│       │   └── ... # other templates
│       └── values.yaml
├── Dockerfile
└── schema.yaml
```

Create a `Dockerfile` at the top level with the following
content:

```Dockerfile
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild
```

Then you can build your container as follows:

```shell
# Set the registry to your project GCR repo.
export REGISTRY=gcr.io/$(gcloud config get-value project | tr ':' '/')
export APP_NAME=wordpress

docker build --tag $REGISTRY/$APP_NAME/deployer .
```

Push your built to the remote GCR so that your app running
in your GKE cluster can access the image:

```shell
docker push $REGISTRY/$APP_NAME/deployer
```

### First deployment

Create a new namespace to cleanly deploy your app:

```shell
kubectl create namespace test-ns

mpdev /scripts/install \
  --deployer=$REGISTRY/$APP_NAME/deployer \
  --parameters='{"name": "test-deployment", "namespace": "test-ns"}'
```

The `install` script simulates what the UI would do deploying your
application. The app parameters are specified in a JSON string here.
In the UI, the user would have configured these parameters in a form.

You can see your application in GKE UI by following this link:

```text
https://console.cloud.google.com/kubernetes/application?project=YOUR_PROJECT
```

### Troubleshooting

The deployer job/pod might fail if your application tries to create
cluster-wide objects, such as `CustomResourceDefinition`, `StorageClass`,
or `ClusterRole` and `ClusterRoleBinding`. This is because the deployer
is only allowed to create namespaced resources.

- `ClusterRole` and `ClusterRoleBinding`: Please see the RBAC section
  in Part 2 below.
- `StorageClass`: If your application uses a storage class, see Part 2
  on how to configure your schema. If your application provides a
  `StorageClass` (i.e. your application is a storage provisioner),
  the resource must be created by the application with a properly
  configured service account. See RBAC section in Part 2 on how to set
  up such a service account.
- Other cluster scoped resources: These resources must be created by
  the application with a properly configured service account. See RBAC
  section in Part 2 on how to set up such a service account.

## Part 1b: Optional: Creating a wrapper chart

One way to import your upstream chart as-is is to create a wrapper
charter. This top level chart has a single dependency which is the
main chart.

**NOTE**: The main caveat here is that existing upstream instructions
for changing the values cannot be used as-is. All values have to be
prefixed with the upstream chart name. See below for more details.

In this example, we create a new `wordpress-mp` chart that uses the
main `wordpress` chart. Create the following directory structure:

```text
.
├── chart
│   └── wordpress-mp
│       ├── Chart.yaml
│       ├── requirements.yaml
│       ├── templates
│       │   └── application.yaml  # Same as in Part 1
│       └── values.yaml
├── Dockerfile                    # Same as in Part 1
└── schema.yaml                   # Same as in Part 1
```

Use the following content for `Chart.yaml`:

```yaml
engine: gotpl
name: wordpress-mp
version: 1.0.0
```

Use the following content for `requirements.yaml`.

```yaml
dependencies:
- name: wordpress
  version: 2.x.x
  repository: https://kubernetes-charts.storage.googleapis.com/
```

For starters, use an empty `values.yaml`. The nice thing about this
file is that values from the upstream chart can be respecified here.
For example, to override `wordpressUsername`, this top level values
file can specify a new value for `wordpress.wordpressUsername`.
For more details, see helm's
[documentation](https://github.com/helm/helm/blob/master/docs/chart_template_guide/subcharts_and_globals.md#overriding-values-from-a-parent-chart).

Run the following helm command to download the wordpress chart.

```shell
helm dependency build chart/wordpress-mp
```

This will add a `charts` directory under `wordpress-mp`. The final
directory structure looks like this:

```text
.
├── chart
│   └── wordpress-mp
│       ├── charts
│       │   └── wordpress-2.1.10.tgz
│       ├── Chart.yaml
│       ├── requirements.lock
│       ├── requirements.yaml
│       ├── templates
│       │   └── application.yaml
│       └── values.yaml
├── Dockerfile
└── schema.yaml
```

You can now rebuild your deployer container and install the
application.

## Part 2: Crafting the schema

`schema.yaml` is a basic JSON schema with Marketplace extensions.
See this [document](schema.md) for more references.

### Declare RBAC requirements (and disable RBAC in the chart)

While helm
[recommends](https://github.com/helm/helm/blob/master/docs/chart_best_practices/rbac.md)
that charts should create RBAC resources by default, Marketplace
requires that charts __must not__ create k8s service accounts or
RBAC resources.

Modify your charts' `values.yaml` to disable service account and RBAC
resource creation. If you created the recommended wrapper chart, you
can easily add override values to do this.

There should be a service account value that the charts take. The
service account is specified under `podSpec` attribute of workload
types, like `Deployment`, `StatefulSet`. Assume it to be
`{{ .Values.controller.serviceAccount }}`, you can add the
following property to your schema.

```yaml
properties:
  controller.serviceAccount:
    type: string
    x-google-marketplace:
      type: SERVICE_ACCOUNT
      serviceAccount:
        roles:
        - type: ClusterRole
          rulesType: PREDEFINED
          rulesFromRoleName: edit
```

(Don't forget to include the name of the subchart if you're modifying
the subchart's value, e.g. `wordpress.controller.serviceAccount` with
our wrapper chart example above.)

At deploy time, the service account with appropriate role bindings is
created by the UI and passed to the deployer. The UI also allows the
end user to select an existing service account instead. In the example
above, a service account with a cluster role `edit` (a system default
cluster role) should be passed to the deployer.

### Parameterize the images

Marketplace solutions must and can only use images that live on
the official `marketplace.gcr.io`. Thus, __all__ images used in
the charts (and subcharts) must be parameterized.

Each image must have a corresponding property. At deployment time,
the official images will be supplied via these properties.

As an example, the following two images are used in the wordpress
chart and its mariadb subchart:

```yaml
# wordpress values.yaml
image:
  registry: docker.io
  repository: bitnami/wordpress
  tag: 4.9.6
---
# mariadb values.yaml
image:
  registry: docker.io
  repository: bitnami/mariadb
  tag: 10.1.33
```

To override wordpress `repository` value, we want this
property name: `image.repository`. To override mariadb
`repository` value, note that it's a subchart, and thus we want
to use `mariadb.image.repository`.

If you following the recommendation of creating a wrapper
chart `wordpress-mp`, the two properties should be
`wordpress.image.repository` and
`wordpress.mariadb.image.repository`. The schema
file should then look something like this:

```yaml
# THIS DOES NOT WORK. READ FURTHER!
properties:
  wordpress.image.repository:
    type: string
    default: bitnami/wordpress   # This is needed.
    x-google-marketplace:        # This annotation is how the system
      type: IMAGE                # knows to pass the image name.
  wordpress.mariadb.image.repository:
    type: string
    default: bitnami/mariadb
    x-google-marketplace:
      type: IMAGE
```

There is one last problem: the images in these charts are specified
by 3 separate components. Marketplace passes the full image name
to a single property (something like
`marketplace.gcr.io/mariadb:10.1.33`). We can use the splitting
feature of the `IMAGE` property type.

```yaml
properties:
  wordpressImage:
    type: string
    default: gcr.io/your-company/wordpress:4.9.6
    x-google-marketplace:
      type: IMAGE
      image:
        generatedProperties:
          splitToRegistryRepoTag:
            registry: wordpress.image.registry
            repo: wordpress.image.repository
            tag: wordpress.image.tag
  mariadbImage:
    type: string
    default: gcr.io/your-company/mariadb:10.1.133
    x-google-marketplace:
      type: IMAGE
      image:
        generatedProperties:
          splitToRegistryRepoTag:
            registry: wordpress.mariadb.image.registry
            repo: wordpress.mariadb.image.repository
            tag: wordpress.mariadb.image.tag
```

Note that `wordpressImage` is also available to your helm chart
as a value `{{ .Values.wordpressImage }}`. The name here can be
arbitrary. `mardiadbImage` is similar.

These image properties __must__ have valid default values. These
tell Marketplace where to find these images and republish them to
the official `marketplace.gcr.io`. These defaults __should__ use
the same GCR repo as your deployer image, as they __should__ be
managed by your build pipeline.

You __should not__ use images that are not under your control.
If your application uses some commonly available image like
`busybox`, make a copy of that image and ensure that it is free
of any vulnerability or malicious code.

Note that end users never see or need access to these default
image names.

_One last reminder_: __all__ images in all charts and subcharts
__must__ be parameterized this way. Only official Marketplace
images are allowed to run in end user's environment.

### Declare parameters user can configure

Reasonable last-mile configuration parameters should be exposed in the
UI form to end users. These parameters should already be in
`values.yaml`. You can add them as properties into the schema.

For example, wordpress `values.yaml` has the following values:

```yaml
wordpressUsername: user
wordpressPassword: null
wordpressBlogName: User's blog
```

Assume you have a wrapper chart created from Part 1b, you can expose
these knobs to the end users as follows:

```yaml
properties:
  wordpress.wordpressBlogName:
    type: string
    default: Your blog name
    description: Enter the name of your blog
  wordpress.wordpressUsername:
    type: string
    default: user
    description: User name to log in to your blog
  wordpress.wordpressPassword:
    type: string
    x-google-marketplace:
      type: GENERATED_PASSWORD
      generatedPassword:
        length: 10
        includeSymbols: True
        base64: False
required:
- wordpress.wordpressBlogName
- wordpress.wordpressUsername
- wordpress.wordpressPassword
```

## Part 3: Crafting application manifest

We follow the standard application resource specified by
[k8s sig-apps](https://github.com/kubernetes-sigs/application).
There are also a few additional guide lines for Marketplace.

A full example of the application manifest can be found
[here](https://github.com/GoogleCloudPlatform/click-to-deploy/blob/master/k8s/cassandra/manifest/application.yaml.template).

### UI

The application manifest drives the deployed application UI:

![Deployer application UI](images/deployed-application.png)

### Application version

As of this writing, we use `v1beta1`. If you change the version
if the application resource, you __must__ update the schema as well.

```yaml
# schema.yaml

applicationApiVersion: v1beta1
```

### Adding an icon

Your application icon should be a PNG of size 200x200.
The binary content of the PNG should be base64 encoded and inlined
into the `icon` field of `application.yaml`.

```yaml
apiVersion: app.k8s.io/v1beta1
kind: Application
metadata:
  annotations:
    kubernetes-engine.cloud.google.com/icon: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIIAAACCCA...
```

Note that k8s API objects have size limits, so a large PNG is
strongly discouraged.

### Marketplace metadata

Add the following annotation. `partner_id` and `product_id` __must__
match the identifiers chosen for the listing. This usually happens
early on in the onboarding process. If you are unsure, contact your
Google partner engineer.

```yaml
kind: Application
metadata:
  annotations:
    marketplace.cloud.google.com/deploy-info: '{partner_id: "your-partner-id", product_id: "your-product-id", partner_name: "Human Friendly Name"}'
```

### Application components

`componentKinds` and `selector` together select the resources
that are considered part of the application. Here is an example:

```yaml
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: "{{ .Release.Name }}"
  componentKinds:
  - group: apps/v1beta2
    kind: Deployment
  - group: batch/v1
    kind: Job
  - group: v1
    kind: PersistentVolumeClaim

```

Note that `app.kubernetes.io/name` is a standard label that is
recommended by k8s sig-apps. This label is automatically applied
on all resources in the chart. Also recall from the schema
specification, the name of the application is also the name of
the helm release.

### Application information table

The information table is useful for showing quick information or
links for the end user to access the application, such as the
application web site.

Here is an example. It defines one entry that references a k8s
`Secret` resource. It also specifies the port and URL path.

```yaml
spec:
  info:
  - name: Blog site (HTTP)
    type: Reference
    valueFrom:
      type: ServiceRef
      serviceRef:
        name: {{ .Values.serviceName }}
        port: 80
        path: /
```

See [InfoItem struct](https://github.com/kubernetes-sigs/application/blob/master/pkg/apis/app/v1beta1/application_types.go)
for more details.

### Application notes

The notes appear on the deployed application page. They are intended
to provide end-user with quick start instructions to start using
the application. They are in Markdown format.

Extended documentation __should not__ be captured in the notes.
Instead, provide links from within the notes. There is also a `links`
section in the application spec.

## Part 4: Finishing touches

### Optional: Using our Makefile

Simplified user commands. Good for CI/CD.

TODO

### Images in staging GCR

The staging GCR hosts all application and deployer images that
Marketplace will copy and republishin into the public
`marketplace.gcr.io`. Images in the staging repo are never
visible to the end users. As an example, let's assume your staging
repo is `gcr.io/your-company/wordpress`.

For each solution, there are always __at least__ one deployer image
and one primary application image. These two have predefined names:
`deployer` and `wordpress`. For this example, let's
say your application uses an additional image called `mariadb`.

Each track of your application is associated with a track tag, which
should be the same name. If you don't know what a track is, see the
general
[onboarding guide](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/set-up-environment#product-identifiers).
See [this section](building-deployer.md#publishing-a-new-version)
for more information about tags. Let's say your application has a
track named `v6`.

Your GCR repo should have the following images:

```text
gcr.io/your-company/wordpress:v6
gcr.io/your-company/wordpress/deployer:v6
gcr.io/your-company/wordpress/mariadb:v6
```

Then your schema should look similar to the following:

```yaml
properties:
  image.primary:
    type: string
    default: gcr.io/your-company/wordpress:v6
    x-google-marketplace:
      type: IMAGE
  image.database:
    type: string
    default: gcr.io/your-company/wordpress/mariadb:v6
    x-google-marketplace:
      type: IMAGE
```

The default values in your schema are important, as this
is how Marketplace knows where to find the application images.

#### CI/CD

Note that all these images share the same registry
(`gcr.io/your-company/wordpress`) and the same tag (`v6`).
To facilitate CI/CD, where you have separate repos and tags
for testing and staging, assuming that you build your deployer
image using the `onbuild` variation of the base deployer,
you can use 2 environment variables `$REGISTRY` and `$TAG`
in your `schema.yaml`. At build time, specify these docker
`ARG`s.

Your schema should look something like this:

```yaml
properties:
  image.primary:
    type: string
    default: $REGISTRY:$TAG
    x-google-marketplace:
      type: IMAGE
  image.database:
    type: string
    default: $REGISTRY/mariadb:$TAG
    x-google-marketplace:
      type: IMAGE
```

The docker build command looks like this:

```shell
docker build \
  --build-arg REGISTRY=gcr.io/your-company/wordpress \
  --build-arg TAG=v6 \
  --tag gcr.io/your-company/wordpress/deployer:v6 .
```

### Running a verification

A verification should be run prior to submission of a version.
Marketplace will do similar verification on our end. A version
must pass all verifications in order to be approved.

Use the following command:

```shell
mpdev /scripts/verify \
  --deployer=gcr.io/your-company/wordpress/deployer:v6
```

This script will create a new test namespace, deploy the app,
verify that it will become healthy, and uninstall it.

If your app requires some additional parameters other than
name and namespace, you can supply them via `--parameters`,
similar to the install command.

### Submitting a version

See [this section](building-deployer.md#publishing-a-new-version).

## Part 5: Integration testing

TODO: Details about our integration tests.
