# Creating a deployer schema

You need a `schema.yaml` file when you [build your deployer](building-deployer.md).

You use the schema file to declare parameter values that users must provide
when they deploy your application to their clusters. The information that users
provide is available to your application when it is deployed.

For example, the schema includes the name of the application instance, the
Kubernetes namespace, service accounts, and so on. Your schema definition is
used to create the form that users see when they deploy the application from
the GCP Console.

The format of `schema.yaml` follows a subset of JSON schema specifications. You
can choose to follow either the `v1` or `v2` specifications for your `schema.yaml`
file. However, if you want to support managed updates for your application, you
must follow the `v2` specification. All applications will be required to follow
the `v2` specification starting in December.

In your deployer image, you must add the schema file to `/data/schema.yaml`.

This is a basic example of a schema.yaml file:

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

Each entry is defined under `properties`, and `required` is a list of required
parameters. The fields that you can define in the schema are described in the
[`schema.yaml` specification](#schemayaml-specification).

All the required fields are validated before the deployment starts.

## Schema and Helm charts

There are a few important notes on how the schema interacts with
the Helm chart:

- Each property defined in the schema maps to a Helm value, as
  as defined in the chart's `values.yaml` file. The properties in the schema
  should be a subset of the keys defined in `values.yaml`.

- User-supplied inputs, as defined by properties in the schema,
  override the default values in `values.yaml`.

- For properties that map to nested fields in `values.yaml`, you can use the
  dot (`.`) notation in your schema.

- In the `x-google-marketplace` section of the schema, `NAME` and `NAMESPACE`
  are always required. These fields map to the Helm chart's `Release.Name` and
  `Release.Namespace` directives respectively.

- The defaults in the schema override the defaults in `values.yaml`.

For example, let's say you have the following `values.yaml` file:

```yaml
database:
  image:
    name: gcr.io/google/mysql:5.6
replicas: 3
```

We can define the following abbreviated schema:

```yaml
properties:
  name:       # maps to Helm's Release.Name directive
    type: string
    x-google-marketplace:
      type: NAME
  namespace:  # maps to Helm's Release.Namespace directive
    type: string
    x-google-marketplace:
      type: NAMESPACE
  replicas:
    type: integer
    default: 3
  database.image.name:  # use a dot to map to the nested field in values.yaml
    type: string
    default: gcr.io/google/mysql:5.6
    x-google-marketplace:
      type: IMAGE
```

## Referencing values from a Helm-based deployer

In Helm charts, you can reference schema parameters similar to value in
`values.yaml`.

For example, this `schema.yaml` gets a `port` from the user:

```yaml
applicationApiVersion: v1beta1
properties:
  port:
    type: integer
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
- port
```

In the Helm chart, you can use the value of `port` in the same way that you
would use a value from `values.yaml`:

```yaml
...
      containers:
        - name: "myContainer"
          image: "myImage"
          ports:
            - name: http
              containerPort: {{ .Values.port }}
...
```

Note that:

- Values defined in `schema.yaml` override values defined in `values.yaml` when
  users deploy your application. For example, if your `values.yaml` contains
  `port: 80`, but a user sets the value of `port` to `21` before deploying, the
  value `21` is used when your application is deployed.

- You can use dots (`.`) to reference nested values. For example, if your
  `values.yaml` looks like this:

    ```yaml
    mysql:
      image: <path to image>
    ```

    You can use the image path in the schema file as `mysql.image`, as in this
    example:

    ```yaml
    applicationApiVersion: v1beta1
    properties:
      mysql.image:
        type: string
    ...
    ```

## Referencing values in an `envsubst`-based deployer

All the parameters defined in `schema.yaml` can be used in your Kubernetes
manifests. To use a parameter, use the name you defined in `schema.yaml`,
prefixed with `$`.

For example, consider this `schema.yaml`:

```yaml
applicationApiVersion: v1beta1
properties:
  port:
    type: string
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
- port
```

To use the value of `port` in the manifest, use `$port`:

```yaml
...
      containers:
        - name: "myContainer"
          image: "myImage"
          ports:
            - name: http
              containerPort: $port
...
```

Schema.yaml v2 specification
---

For an example of a `v2` `schema.yaml`, refer to [this sample schema](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/tests/marketplace/deployer_envsubst_base/standard_v2/schema.yaml).

All `schema.yaml` files will be required to be `v2` starting in December of this year.

## `properties`

The `properties` section contains the fields that users see in the GCP Console
when they deploy your app. For each property, you can define the following
sub-properties.

### `title`

The text shown in the in the GCP Marketplace UI when users configure their
deployment.

![Custom property in the UI](images/custom-property-ui.png)

### `type`

The data type of the property. The supported types are:

- `string`
- `integer`
- `boolean`

### `description`

A short description of the property, shown as a tooltip in the interface.
If the description requires more than a paragraph, consider adding more detail
in your user guides.

### `default`

A default value to use for the property, if users don't provide a value.

### `enum`

A list of valid values for the property, shown as a drop-down menu. Use the
following syntax to define your list:

```yaml
  testProperty:
    type: string
    title: Test property
    description: My Test Property
    enum:
    - 'Value 1'
    - 'Value 2'
    - 'Value 3'
```

![Enum property UI](images/enum-property-ui.png)

### `minimum`

If the property is a number, the minimum value that users must enter.
The value has to be greater than or equal to `minimum`.

### `maximum`

If the property is a number, the maximum value that users can enter.
The value has to be less than or equal to `maximum`.

### `maxLength`

For `string` properties, the maximum length of the value.

### `pattern`

A regex pattern. The value needs to match `pattern`.

### `x-google-marketplace`

An annotation that indicates that the property has a specific role and needs
to be handled by GCP Marketplace in a special way. Here is an example of a top-level
`x-google-marketplace` section:

```yaml
x-google-marketplace:
  # MUST be v2.
  schemaVersion: v2

  # MUST match the version of the Application custom resource object.
  # This is the same as the top level applicationApiVersion field in v1.
  applicationApiVersion: v1beta1

  # The release version is required in the schema and MUST match the
  # release tag on the the deployer.
  publishedVersion: '0.1.1'
  publishedVersionMetadata:
    releaseNote: >-
      Initial release.
    # releaseTypes list is optional.
    # "Security" should only be used if this is an important update to patch
    # an existing vulnerability, as such updates will display more prominently for users.
    releaseTypes:
    - Feature
    - BugFix
    - Security
    # If "recommended" is "true", users using older releases are encouraged
    # to update as soon as possible. This is useful if, for example, this release
    # fixes a critical issue.
    recommended: true

  # This MUST be specified to indicate that the deployer supports managed updates.
  # Note that this could be left out or kalmSupported set to false, in
  # which case the deployer uses schema v2 but does not support update.
  managedUpdates:
    kalmSupported: true

  # Image declaration is required here. See the Images section below.
  images: {}

  # Other fields like clusterConstraints can be included here.

# properties and required sections remain the same.
```

When you add this annotation,
you must also specify a `type`, described in
[`x-google-marketplace`](#x-google-marketplace-1).

---
## `x-google-marketplace`

Use the following types to indicate how the properties in your schema are
treated by GCP Marketplace.

### `schemaVersion`

The version of the schema. If you want to
[support managed updates for your app](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/support-managed-updates), the value must be `v2`.

### (Required) `applicationApiVersion`

The version of the Application Custom Resource object. As of November 2019,
the version is `v1beta1`.

### (Required) `publishedVersion`

The
[release version for the application](docs/building-deployer.md#tagging-your-deployer-image),
as a string. This must match the release tag on all your application images. For
example, `'1.0.5'`.

### `publishedVersionMetadata`

Information about the version, shown to users in the GCP Console when they
view their Kubernetes workloads.

#### `releaseNote`

Information about the release, using the
[YAML folding style, with a block chomping indicator](https://yaml-multiline.info).
For example:

```yaml
releaseNote: >-
  Bug fixes and performance enhancements.
```

#### (Optional) `releaseTypes`

A list of release types, which can be one or more of the following:

- `Feature`
- `BugFix`
- `Security`. We recommend using `Security` only if the update addresses a
  critical security issue. In the GCP Console, security updates are displayed
  more prominently than other types of updates.

#### `recommended`

A boolean that indicates whether the update is recommended, such as for a
security update. If `true`, users are encouraged to update as soon as possible.

### `managedUpdates`

Use this section to indicate that your deployer supports managed updates. If
you omit this section, users must manually update their installations.

#### `kalmSupported`

If you want to support managed updates for your application, set this to
`true`.

### `images`

Use this section to declare the images for your application.

Here is an example `images` section:

```yaml
  images:
    '':  # Primary image has no name and is required.
    proxy: {}
      properties:
        imageRepo:
          type: REPO_WITH_REGISTRY
        imageTag:
          type: TAG
    init:
      properties:
        imageInitFull:
          type: FULL
        imageInitRegistry:
          type: REGISTRY
        imageInitRepo:
          type: REPO_WITHOUT_REGISTRY
        imageInitTag:
          type: TAG
```

This example section declares two images, in addition to the deployer:

`gcr.io/your-project/your-company/your-app:1.0.1`
`gcr.io/your-project/your-company/your-app/proxy:1.0.1`

Their names are set as declared within the `images` section; their shared
prefix is set externally to the `schema.yaml` file.

The images can be passed as parameters or values to your application templates
or charts (as applicable) by using the `properties` section. Each property
can pass either the full image name or a specific part of it, depending on
its assigned `type`:

- `FULL` passes the entire image name,
  `gcr.io/your-project/your-company/your-app:1.0.1`
- `REGISTRY` only passes the initial `gcr.io`
- `REPO_WITHOUT_REGISTRY` passes only the repo, without the registry or tag,
  which would be `your-project/your-company/your-app`
- `REPO_WITH_REGISTRY` passes the repo, with the registry and without the
  tag, which would be `gcr.io/your-project/your-company/your-app`
- `TAG` only passes the image tag, which in this case is `1.0.1`

In the earlier example, the `proxy` image is passed to the template with
the following values:

- `imageProxyFull=gcr.io/your-project/your-company/your-app:1.0.1`
- `imageProxyRegistry=gcr.io`
- `imageProxyRepo=your-project/your-company/your-app`
- `imageProxyTag=1.0.1`

The primary image above is passed under 2 different parameters/values:

- `imageRepo=gcr.io/your-project/your-company/your-app`
- `imageTag=1.0.1`

Note that when users deploy your app from GCP Marketplace, the final image
names are different, but follow the same release tag and name prefix rule. For
example, the published images could be under:

- `marketplace.gcr.io/your-company/your-app:1.0.1`
- `marketplace.gcr.io/your-company/your-app/deployer:1.0.1`
- `marketplace.gcr.io/your-company/your-app/init:1.0.1`

### `type`

Defines how the property must be handled by GCP Marketplace. Each type has a
different set of properties.

#### Supported types

- `NAME`: Indicates that the property is the name of the app.
- [`NAMESPACE`](#type-namespace): Indicates that the property is the Kubernetes
  namespace where the app will installed.
- `REPORTING_SECRET`: The Secret resource name that contains the credentials
  for usage reports. These credentials are used by the
  [usage-based billing agent](https://github.com/GoogleCloudPlatform/ubbagent).
- [`MASKED_FIELD`](#type-masked_field): A string value whose characters will be masked when entered in the UI.
- [`GENERATED_PASSWORD`](#type-generated_password): Indicates that the property
  is a value to be generated when the application is deployed.
- [`SERVICE_ACCOUNT`](#type-service_account): The name of a pre-provisioned
  Kubernetes `ServiceAccount`. If the ServiceAccount does not exist, a new one
  is created when users deploy the application.
- [`STORAGE_CLASS`](#type-storage_class): The name of a pre-provisioned
  Kubernetes `StorageClass`. If the StorageClass does not exist, a new one is
  created when users deploy the application.
- [`STRING`](#type-string): A string that needs special handling, such as a
  string that is base64-encoded.
- [`APPLICATION_UID`](#type-application_uid): The UUID of the created
  `Application` object.
- [`ISTIO_ENABLED`](#type-istio_enabled): Indicates whether [Istio](https://istio.io)
  is enabled on the cluster for the deployment.
- [`INGRESS_AVAILABLE`](#type-ingress_available): Indicates whether the cluster is detected to have Ingress support.
- [`TLS_CERTIFICATE`](#type-tls_certificate): To be used to support a custom certificate or generate a self-signed certificate.

---

### type: MASKED_FIELD

Indicates that the property where the value that the user enters must be
masked. Use this annotation for fields such as passwords chosen by the user.
In the GCP Marketplace UI, users will also see an option to reveal the
value as plain text.

Example:

```yaml
properties:
  customSecret:
    title: User-specified password
    description: The password to be used for login.
    maxLength: 32
    type: string
    x-google-marketplace:
      type: MASKED_FIELD
```
---

### type: NAMESPACE

This property is required. It specifies the target namespace where all of application
resources are installed into.

A `default` value can be specified, in which case the UI will auto-select this
namespace instead of using the default heuristics of picking or creating a namespace.

```yaml
properties:
  namespace:
    type: string
    default: desired-fixed-namespace
    x-google-marketplace:
      type: NAMESPACE
```

---

### type: GENERATED_PASSWORD

Example:

```yaml
properties:
  dbPassword:
    type: string
    x-google-marketplace:
      type: GENERATED_PASSWORD
      generatedPassword:
        length: 16
        includeSymbols: False  # Default is False
        base64: True           # Default is True
```

- `includeSymbols` if `True`, the special characters are included in the generated password.
- `base64` if `True`, the generated password is passed as a base64-encoded value. This means it can be used directly in a `Secret` manifest. If the value is to be encoding in your helm template, this property should be set to `False`.

---

### type: SERVICE_ACCOUNT

All service accounts need to be defined as parameters in `schema.yaml`.

If you add a Kubernetes `ServiceAccount` as a resource in your manifest, the
deployment fails with an authentication error, because the deployer doesn't run
with enough privileges to create a Service Account.

For example, the following `schema.yaml` snippet adds a Service Account with
Cluster Roles:

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
            resources: ['applications']
            verbs: ['*']
        - type: ClusterRole
          rulesType: CUSTOM
          rules:
          - apiGroups: ['etcd.database.coreos.com/v1beta2']
            resources: ['etcdclusters']
            verbs: ['*']
```

---

### type: STORAGE_CLASS

All Storage Classes need to be defined as parameters in `schema.yaml`.

If you add a Kubernetes `StorageClass` as a resource in your manifest, the
deployment fails with an authentication error, because the deployer doesn't run
with enough privileges to create a Storage Class.

For example, this `schema.yaml` snippet creates a Storage Class:

```yaml
properties:
  ssdStorageClass:
    type: string
    x-google-marketplace:
      type: STORAGE_CLASS
      storageClass:
        type: SSD
```

The created `StorageClass` has the name `<namespace>-<app_name>-<property_name>`.

---

### type: STRING

This is used to represent a string that needs special handling. For example,
if a string is base64 encoded.

Example:

```yaml
properties:
  explicitPassword:
    type: string
    x-google-marketplace:
      type: STRING
      string:
        generatedProperties:
          base64Encoded: explicitPasswordEncoded
```

In the example above, manifests can reference the password as
`explicitPassword`, and its base64Encoded value as `explicitPasswordEncoded`.

---

### type: APPLICATION_UID

When the deployer runs, a placeholder `Application` object is created.
A property annotated with `APPLICATION_UID` gets the object's UUID.

Your template must handle the following two scenarios:

- If the value for the property is `false` or empty, the template must
  include an `Application` object in the manifest. This object is applied
  to update the placeholder.

- If the value for the property is a UUID, the template must
  NOT include an `Application` object in its manifest.

If you are using Helm, do not include the `Application` object in the manifest.

Some tools, including Helm, stop the deployment if an object in the manifest
already exists, so the installation fails because of the placeholder
`Application`.

Use the following syntax to declare the UUID in `schema.yaml`:

```yaml
properties:
  appUid:
    type: string
    x-google-marketplace:
      type: APPLICATION_UID
      applicationUid:
        generatedProperties:
          createApplicationBoolean: global.application.create
```

- `createApplicationBoolean`: Indicates the property that gets the boolean
  value. You can use the boolean in the template to determine whether to
  include an `Application` resource in the manifest.

  If you're using Helm, in the Helm chart, you can do one of the following:

  ```yaml
  {{- if not .Values.application_uid }}
  # Application object definition
  {{- end }}

  # OR ...

  {{- if .Values.global.application.create }}  # declared in createApplicationBoolean
  # Application object definition
  {{- end }}
  ```

---

### type: ISTIO_ENABLED

This boolean property is True if the environment has [Istio](https://istio.io/)
enabled, and False otherwise. The deployer and template can use this signal to
adapt the deployment accordingly.

[Review the limitations for GCP Marketplace apps on clusters that run Istio](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/create-app-package#istio-limitations).

---

### type: INGRESS_AVAILABLE

This boolean property is True if the cluster has an Ingress controller. The
deployer and template can use this signal to adapt the deployment accordingly.

---

### type: TLS_CERTIFICATE

This property provides an SSL/TLS certificate for the Kubernetes manifest. By
default, a self-signed certificate is generated.

The example below shows the syntax to declare a certificate:

```yaml
properties:
  certificate:
    type: string
    x-google-marketplace:
      type: TLS_CERTIFICATE
      tlsCertificate:
        generatedProperties:
          base64EncodedPrivateKey: TLS_CERTIFICATE_KEY
          base64EncodedCertificate: TLS_CERTIFICATE_CRT
```

Where:

* `base64EncodedPrivateKey` indicates the property that gets the private key.
* `base64EncodedCertificate` indicates the property that gets the certificate.

You can provide a custom certificate by overwriting the `certificate` property
in the following JSON format:

```json
{
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
  "certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
}
```

If you're using a Helm chart, you can handle the certificate in the following
way:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
  namespace: demo
data:
  tls.key: {{ .Values.TLS_CERTIFICATE_KEY }}
  tls.crt: {{ .Values.TLS_CERTIFICATE_CRT }}
type: kubernetes.io/tls
```

If you're using an `envsubst` manifest, you can handle the certificate in the
following way:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
  namespace: demo
data:
  tls.key: $TLS_CERTIFICATE_KEY
  tls.crt: $TLS_CERTIFICATE_CRT
type: kubernetes.io/tls
```

---

## clusterConstraints

Use `clusterConstraints` to specify the requirements for the Kubernetes
cluster. The requirements determine whether your application can be run on
the cluster. For example, you can specify that the cluster must be set up to
run a minimum number of replicas.

For example, the following `schema.yaml` specifies that the cluster must have
3 nodes, 256 MiB of memory, and 500 CPU millicores (0.5 CPU cores):

```yaml
properties:
  # Property definitions...
required:
  # Required properties...
x-google-marketplace:
  clusterConstraints:
    resources:
    - replicas: 3
      requests:
        cpu: 500m
        memory: 256Mi
      affinity:
        simpleNodeAffinity:
          type: REQUIRE_ONE_NODE_PER_REPLICA
```

Each entry under `resources` is roughly equivalent to a workload in the
application.

* `affinity` defines the relationship between the nodes and the replicas.

    * `simpleNodeAffinity` is an affinity definition. It has 2 types:

        * `REQUIRE_ONE_NODE_PER_REPLICA`: The number of nodes must be at least
          the same as the number of replicas, so that each replica is scheduled
          on a different node.
        * `REQUIRE_MINIMUM_NODE_COUNT`: The minimum number of nodes must be
          specified separately in `minimumNodeCount`. For example:

```yaml
x-google-marketplace:
  clusterConstraints:
    resources:
    - replicas: 5
      requests:
        cpu: 500m
      affinity:
        simpleNodeAffinity:
          type: REQUIRE_MINIMUM_NODE_COUNT
          minimumNodeCount: 3
```

---

### istio

Use this property to indicate compatibility between the app and the Istio
service mesh installation in the cluster.

```yaml
properties:
  # Property definitions...
required:
  # Required properties...
x-google-marketplace:
  clusterConstraints:
    istio:
      type: OPTIONAL | REQUIRED | UNSUPPORTED
```

If this property is not specified, users see a warning when the app is deployed
to an Istio-enabled environment. The [`ISTIO_ENABLED`](#type-istio_enabled)
indicates whether Istio is enabled on the cluster.

#### Supported types

- `OPTIONAL`: The app works with Istio but does not require it.
- `REQUIRED`: The app requires Istio to work properly.
- `UNSUPPORTED`: The app does not support Istio.

Schema.yaml v1 specification
---

For an example of a `v1` `schema.yaml`, refer to [this sample schema](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/tests/marketplace/deployer_envsubst_base/standard/schema.yaml).

Applications will be required to use `v2` `schema.yaml` files starting in December 2019.

## `applicationApiVersion`

Specifies the version of the [Application](https://github.com/kubernetes-sigs/application) CRD.

GCP Marketplace supports version `v1beta1` and later.

## `properties`

The `properties` section contains the fields that users see in the GCP Console when they deploy your app. For each property, you can define the following sub-properties.

### `title`

The text shown in the in the GCP Marketplace UI when users configure their
deployment.

![Custom property in the UI](images/custom-property-ui.png)

### `type`

The data type of the property. The supported types are:

- `string`
- `integer`
- `boolean`

### `description`

A short description of the property, shown as a tooltip in the interface.
If the description requires more than a paragraph, consider adding more detail
in your user guides.

### `default`

A default value to use for the property, if users don't provide a value.

### `enum`

A list of valid values for the property, shown as a drop-down menu. Use the
following syntax to define your list:

```yaml
  testProperty:
    type: string
    title: Test property
    description: My Test Property
    enum:
    - 'Value 1'
    - 'Value 2'
    - 'Value 3'
```

![Enum property UI](images/enum-property-ui.png)

### `minimum`

If the property is a number, the minimum value that users must enter.
The value must be greater than or equal to `minimum`.

### `maximum`

If the property is a number, the maximum value that users can enter.
The value must be less than or equal to `maximum`.

### `maxLength`

For `string` properties, the maximum length of the value.

### `pattern`

A regex pattern. The value needs to match `pattern`.

### `x-google-marketplace`

An annotation that indicates that the property has a specific role and needs
to be handled by GCP Marketplace in a special way. When you add this annotation,
you must also specify a `type`, described in
[`x-google-marketplace`](#x-google-marketplace-1).

---
## `x-google-marketplace`

Use the following types to indicate how the properties in your schema are
treated by GCP Marketplace.

### `type`

Defines how the property must be handled by GCP Marketplace. Each type has a
different set of properties.

#### Supported types

- `NAME`: Indicates that the property is the name of the app.
- [`NAMESPACE`](#type-namespace): Indicates that the property is the Kubernetes
  namespace where the app will installed.
- `REPORTING_SECRET`: The Secret resource name that contains the credentials
  for usage reports. These credentials are used by the
  [usage-based billing agent](https://github.com/GoogleCloudPlatform/ubbagent).
- [`MASKED_FIELD`](#type-masked_field): A string value whose characters will be masked when entered in the UI.
- [`GENERATED_PASSWORD`](#type-generated_password): Indicates that the property
  is a value to be generated when the application is deployed.
- [`SERVICE_ACCOUNT`](#type-service_account): The name of a pre-provisioned
  Kubernetes `ServiceAccount`. If the ServiceAccount does not exist, a new one
  is created when users deploy the application.
- [`STORAGE_CLASS`](#type-storage_class): The name of a pre-provisioned
  Kubernetes `StorageClass`. If the StorageClass does not exist, a new one is
  created when users deploy the application.
- [`STRING`](#type-string): A string that needs special handling, such as a
  string that is base64-encoded.
- [`IMAGE`](#type-image): Indicates that the property is a link to a Docker image.
- [`APPLICATION_UID`](#type-application_uid): The UUID of the created
  `Application` object.
- [`ISTIO_ENABLED`](#type-istio_enabled): Indicates whether [Istio](https://istio.io)
  is enabled on the cluster for the deployment.
- [`INGRESS_AVAILABLE`](#type-ingress_available): Indicates whether the cluster is detected to have Ingress support.
- [`TLS_CERTIFICATE`](#type-tls_certificate): To be used to support a custom certificate or generate a self-signed certificate.

---

### type: MASKED_FIELD

Indicates that the property where the value that the user enters must be
masked. Use this annotation for fields such as passwords chosen by the user.
In the GCP Marketplace UI, users will also see an option to reveal the
value as plain text.

Example:

```yaml
properties:
  customSecret:
    title: User-specified password
    description: The password to be used for login.
    maxLength: 32
    type: string
    x-google-marketplace:
      type: MASKED_FIELD
```
---

### type: NAMESPACE

This property is required. It specifies the target namespace where all of application
resources are installed into.

A `default` value can be specified, in which case the UI will auto-select this
namespace instead of using the default heuristics of picking or creating a namespace.

```yaml
properties:
  namespace:
    type: string
    default: desired-fixed-namespace
    x-google-marketplace:
      type: NAMESPACE
```

---

### type: GENERATED_PASSWORD

Example:

```yaml
properties:
  dbPassword:
    type: string
    x-google-marketplace:
      type: GENERATED_PASSWORD
      generatedPassword:
        length: 16
        includeSymbols: False  # Default is False
        base64: True           # Default is True
```

- `includeSymbols` if `True`, the special characters are included in the generated password.
- `base64` if `True`, the generated password is passed as a base64-encoded value. This means it can be used directly in a `Secret` manifest. If the value is to be encoding in your helm template, this property should be set to `False`.

---

### type: SERVICE_ACCOUNT

All service accounts need to be defined as parameters in `schema.yaml`.

If you add a Kubernetes `ServiceAccount` as a resource in your manifest, the
deployment fails with an authentication error, because the deployer doesn't run
with enough privileges to create a Service Account.

For example, the following `schema.yaml` snippet adds a Service Account with
Cluster Roles:

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
            resources: ['applications']
            verbs: ['*']
        - type: ClusterRole
          rulesType: CUSTOM
          rules:
          - apiGroups: ['etcd.database.coreos.com/v1beta2']
            resources: ['etcdclusters']
            verbs: ['*']
```

---

### type: STORAGE_CLASS

All Storage Classes need to be defined as parameters in `schema.yaml`.

If you add a Kubernetes `StorageClass` as a resource in your manifest, the
deployment fails with an authentication error, because the deployer doesn't run
with enough privileges to create a Storage Class.

For example, this `schema.yaml` snippet creates a Storage Class:

```yaml
properties:
  ssdStorageClass:
    type: string
    x-google-marketplace:
      type: STORAGE_CLASS
      storageClass:
        type: SSD
```

The created `StorageClass` has the name `<namespace>-<app_name>-<property_name>`.

---

### type: STRING

This is used to represent a string that needs special handling. For example,
if a string is base64 encoded.

Example:

```yaml
properties:
  explicitPassword:
    type: string
    x-google-marketplace:
      type: STRING
      string:
        generatedProperties:
          base64Encoded: explicitPasswordEncoded
```

In the example above, manifests can reference the password as
`explicitPassword`, and its base64Encoded value as `explicitPasswordEncoded`.

---

### type: IMAGE

Define an `IMAGE` type property for each image used by the application,
other than the deployer image itself. Set the default property value to the
image in your staging GCR repository. This property indicates which images should
be published as a part of your application, and ensures that the
correct published images are used when users deploy the app from the
GCP Marketplace UI.

---

### type: APPLICATION_UID

When the deployer runs, a placeholder `Application` object is created.
A property annotated with `APPLICATION_UID` gets the object's UUID.

Your template must handle the following two scenarios:

- If the value for the property is `false` or empty, the template must
  include an `Application` object in the manifest. This object is applied
  to update the placeholder.

- If the value for the property is a UUID, the template must
  NOT include an `Application` object in its manifest.

If you are using Helm, do not include the `Application` object in the manifest.

Some tools, including Helm, stop the deployment if an object in the manifest
already exists, so the installation fails because of the placeholder
`Application`.

Use the following syntax to declare the UUID in `schema.yaml`:

```yaml
properties:
  appUid:
    type: string
    x-google-marketplace:
      type: APPLICATION_UID
      applicationUid:
        generatedProperties:
          createApplicationBoolean: global.application.create
```

- `createApplicationBoolean`: Indicates the property that gets the boolean
  value. You can use the boolean in the template to determine whether to
  include an `Application` resource in the manifest.

  If you're using Helm, in the Helm chart, you can do one of the following:

  ```yaml
  {{- if not .Values.application_uid }}
  # Application object definition
  {{- end }}

  # OR ...

  {{- if .Values.global.application.create }}  # declared in createApplicationBoolean
  # Application object definition
  {{- end }}
  ```

---

### type: ISTIO_ENABLED

This boolean property is True if the environment has [Istio](https://istio.io/)
enabled, and False otherwise. The deployer and template can use this signal to
adapt the deployment accordingly.

[Review the limitations for GCP Marketplace apps on clusters that run Istio](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/create-app-package#istio-limitations).

---

### type: INGRESS_AVAILABLE

This boolean property is True if the cluster has an Ingress controller. The
deployer and template can use this signal to adapt the deployment accordingly.

---

### type: TLS_CERTIFICATE

This property provides an SSL/TLS certificate for the Kubernetes manifest. By
default, a self-signed certificate is generated.

The example below shows the syntax to declare a certificate:

```yaml
properties:
  certificate:
    type: string
    x-google-marketplace:
      type: TLS_CERTIFICATE
      tlsCertificate:
        generatedProperties:
          base64EncodedPrivateKey: TLS_CERTIFICATE_KEY
          base64EncodedCertificate: TLS_CERTIFICATE_CRT
```

Where:

* `base64EncodedPrivateKey` indicates the property that gets the private key.
* `base64EncodedCertificate` indicates the property that gets the certificate.

You can provide a custom certificate by overwriting the `certificate` property
in the following JSON format:

```json
{
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
  "certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
}
```

If you're using a Helm chart, you can handle the certificate in the following
way:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
  namespace: demo
data:
  tls.key: {{ .Values.TLS_CERTIFICATE_KEY }}
  tls.crt: {{ .Values.TLS_CERTIFICATE_CRT }}
type: kubernetes.io/tls
```

If you're using an `envsubst` manifest, you can handle the certificate in the
following way:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
  namespace: demo
data:
  tls.key: $TLS_CERTIFICATE_KEY
  tls.crt: $TLS_CERTIFICATE_CRT
type: kubernetes.io/tls
```

---

## clusterConstraints

Use `clusterConstraints` to specify the requirements for the Kubernetes
cluster. The requirements determine whether your application can be run on
the cluster. For example, you can specify that the cluster must be set up to
run a minimum number of replicas.

For example, the following `schema.yaml` specifies that the cluster must have
3 nodes, 256 MiB of memory, and 500 CPU millicores (0.5 CPU cores):

```yaml
properties:
  # Property definitions...
required:
  # Required properties...
x-google-marketplace:
  clusterConstraints:
    resources:
    - replicas: 3
      requests:
        cpu: 500m
        memory: 256Mi
      affinity:
        simpleNodeAffinity:
          type: REQUIRE_ONE_NODE_PER_REPLICA
```

Each entry under `resources` is roughly equivalent to a workload in the
application.

* `affinity` defines the relationship between the nodes and the replicas.

    * `simpleNodeAffinity` is an affinity definition. It has 2 types:

        * `REQUIRE_ONE_NODE_PER_REPLICA`: The number of nodes must be at least
          the same as the number of replicas, so that each replica is scheduled
          on a different node.
        * `REQUIRE_MINIMUM_NODE_COUNT`: The minimum number of nodes must be
          specified separately in `minimumNodeCount`. For example:

```yaml
x-google-marketplace:
  clusterConstraints:
    resources:
    - replicas: 5
      requests:
        cpu: 500m
      affinity:
        simpleNodeAffinity:
          type: REQUIRE_MINIMUM_NODE_COUNT
          minimumNodeCount: 3
```

---

### istio

Use this property to indicate compatibility between the app and the Istio
service mesh installation in the cluster.

```yaml
properties:
  # Property definitions...
required:
  # Required properties...
x-google-marketplace:
  clusterConstraints:
    istio:
      type: OPTIONAL | REQUIRED | UNSUPPORTED
```

If this property is not specified, users see a warning when the app is deployed
to an Istio-enabled environment. The [`ISTIO_ENABLED`](#type-istio_enabled)
indicates whether Istio is enabled on the cluster.

#### Supported types

- `OPTIONAL`: The app works with Istio but does not require it.
- `REQUIRED`: The app requires Istio to work properly.
- `UNSUPPORTED`: The app does not support Istio.
