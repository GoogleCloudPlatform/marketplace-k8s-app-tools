# Deployer Schema

The `schema.yaml` file is the way to declare parameter values that end-user needs to provide
in order to provision the application. For example, the name of the application, the kubernetes
namespace, service accounts, etc. It follows a more strict subset of JSON schema specifications.
The UI uses `schema.yaml` to render the form that end-users will interact with to configure and
deploy the application.

The information provided by the user for properties defined in `schema.yaml` is available at deployment time.

The schema file must exist at the well known location `/data/schema.yaml` in the deployer image.

This is a simple example of a schema.yaml file:

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

Each entry is defined inside properties, and `required` is a list of required parameters.
We validate that all required fields are provided before starting the deployment.

## Schema and helm chart

There are a few important notes on how the schema interacts with
the helm chart:

- Each property defined in the schema effectively maps to a helm value as
  as defined in the chart's `values.yaml` file. This set of properties
  **should** be a subset of the keys defined in `values.yaml`.
- User-supplied inputs, as defined by properties in the schema, effectively
  override the default values in `values.yaml`.
- The dot annotation can be used to name properties that map to a nested
  field inside a hierarchical `values.yaml`.
- There are two required special properties of `x-google-marketplace` types
  `NAME` and `NAMESPACE` in every schema. These map to the required helm's
  release name and namespace.
- The defaults in the schema can be different from and will override the
  defaults in `values.yaml`.

As an example, let's say we have the following `values.yaml` file:

```yaml
database:
  image:
    name: gcr.io/google/mysql:5.6
replicas: 3
```

We can define the following abbreviated schema:

```yaml
properties:
  name:       # maps to helm release name
    type: string
    x-google-marketplace:
      type: NAME
  namespace:  # maps to helm release namespace
    type: string
    x-google-marketplace:
      type: NAMESPACE
  replicas:
    type: integer
    default: 3
  database.image.name:
    type: string
    default: gcr.io/google/mysql:5.6
    x-google-marketplace:
      type: IMAGE
```

## Referencing `schema.yaml` parameter values in kubernetes manifests

All parameters defined in `schema.yaml` can be used in manifests.

### Helm based deployer

They can be referenced in helm charts just like a regular value from `values.yaml`.

Example of `schema.yaml`

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

Usage example of the value of `port` in a helm chart:

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

Notice that:
- Values defined in `schema.yaml` will overlay values defined in `values.yaml`. For example, if
`values.yaml` looks like the following:

```yaml
port: 80
```

but the value of `port` is set to 21 by the user, the value 21 will be used.

- Dots can be used for referencing nested values. For example, if the app makes use of
`values.yaml` like below:

```yaml
mysql:
  image: <path to image>
```

the property can be referenced in the schema file as `mysql.image`

```yaml
applicationApiVersion: v1beta1
properties:
  mysql.image:
    type: string
...
```

### Envsubst based deployer

They can be referenced in manifests by its name in `schema.yaml`, prefixed with `$`.

Example of `schema.yaml`

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

Usage example of the value of `port` in a helm chart:

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

Schema.yaml specification
---

## applicationApiVersion

Specifies the version of the application CRD.

Supports versions starting from `v1beta1`.

## Properties

### type

Represents the type of the input in the form for that property.

#### Supported types
- `string`
- `integer`
- `boolean`

### title

Displayed text in the ui.

### description

Explanation of what the property is or what is used for. Be mindful of good explanation as a way to improve user experience.

### default

If user does not provide a value, `default` will be used.

### minimum

The value has to be greater or equal than `minimum`.

### maximum

The value has to be less or equal than `maximum`.

### maxLength

The value length has to be less or equal than `maxLength`.

### pattern

A regex pattern. The value needs to match `pattern`.

### x-google-marketplace

This serves as an annotation to tell gcp to handle that property in a special way, depending on `type`.
It has several usages and more will be added based on demand.

### [Examples](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-example/blob/master/wordpress/schema.yaml).

---
## x-google-marketplace

### type

It defines how this object will be handled. Each type has a different set of properties.

#### Supported types
- `NAME`: To be used as the name of the app.
- `NAMESPACE`: To be used as the kubernetes namespace where the app will installed.
- `IMAGE`: Link to a docker image.
- `GENERATED_PASSWORD`: A value to be generated at deployment time, following common password requirements.
- `REPORTING_SECRET`: The Secret resource name containing the usage reporting credentials
- `SERVICE_ACCOUNT`: The name of a pre-provisioned k8s `ServiceAccount`. If it does not exist, one is created.
- `STORAGE_CLASS`: The name of a pre-provisioned k8s `StorageClass`. If it does not exist, one is created.
- `STRING`: A string that needs special handling.

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
        includeSymbols: False  # Default is False
        base64: True           # Default is True
```

- `includeSymbols` if `True`, the special characters are included in the generated password.
- `base64` if `True`, the generated password is passed as a base64-encoded value. This means it can be used directly in a `Secret` manifest. If the value is to be encoding in your helm template, this property should be set to `False`.

---

### type: SERVICE_ACCOUNT

Defining a `ServiceAccount` as a resource to be deployed will cause deployer to fail with authentication errors,
because the deployer doesn't run with privileges that allow creating them.
All service accounts need to be defined as parameters in `schema.yaml`.

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

Defining a `StorageClass` as a resource to be deployed will cause deployer to fail with authentication errors,
because the deployer doesn't run with privileges that allow creating them.
All storage classes need to be defined as parameters in `schema.yaml`.

```yaml
properties:
  ssdStorageClass:
    type: string
    x-google-marketplace:
      type: STORAGE_CLASS
      storageClass:
        type: SSD
```

### type: STRING

This is used to represent a string that needs special handling, for example base64 representation.

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

In the example above, manifests can reference to the password as `explicitPassword`, as well as to its base64Encoded value as `explicitPasswordEncoded`.

## clusterConstraints

Nested under `x-google-marketplace`, this can be used for specifying constraints on the kubernetes cluster. These constraints help determine if the application can be successfully deployed to the cluster. The UI can filter out ineligible clusters following these constraints.

Example:

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

The above example requires a cluster with at least three nodes, each with compute resources for running one pod requiring 500 milicores of CPU and 256MiB of memory.

Each entry under `resources` is roughly equivalent to a workload in the application.

`affinity` defines the relationship between the nodes and the replicas. `simpleNodeAffinity` is the only affinity definition we currently support. It has 2 types:
- `REQUIRE_ONE_NODE_PER_REPLICA`: each replica must be scheduled on a different node. i.e. the number of nodes must be at least the number of replicas.
- `REQUIRE_MINIMUM_NODE_COUNT`: the minimum number of nodes is specified separately in `minimumNodeCount`. For example:

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
