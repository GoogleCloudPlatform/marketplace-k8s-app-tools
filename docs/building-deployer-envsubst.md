# Building Envsubst Deployer

## Prerequisites

See [this doc](tool-prerequisites.md).

## Part 1: Up and Running

The goal of this step is to build the minimal deployer to deploy a kubernetes
application.

In this tutorial, we set up a basic `nginx` service.

The directory structure for the minimal deployer will look as below:
```text
.
├── manifest
|   ├── manifests.yaml.template
|   └── application.yaml.template
├── Dockerfile
├── schema.yaml
```

### Create the initial schema

Create a `schema.yaml` at the top level. Use the following content:

```yaml
x-google-marketplace:
  schemaVersion: v2

  applicationApiVersion: v1beta1
  # The published version is required and MUST match the tag
  # of the deployer image
  publishedVersion: '0.1.1'
  publishedVersionMetadata:
    releaseNote: >-
      A first release.
  # The images property will be filled in during part 2
  images: {}

properties:
  name:
    type: string
    x-google-marketplace:
      type: NAME
  namespace:
    type: string
    x-google-marketplace:
      type: NAMESPACE
  replicas:
    type: integer
    title: Nginx Replica Count
    description: The number of nginx replicas to deploy

required:
- name
- namespace
- replicas
```

The `name` and `namespace` properties are required for all applications, and
require the `x-google-marketplace.type` fields as shown above. The `replicas`
property is application specific and in this demo will define how many nginx
replicas to deploy. The `title` and `description` fields under the `replicas`
property are presented in the Google Cloud Marketplace UI when users configure
their deployment. The user will also be able to specify the `name` of the
application and the `namespace` where the k8s application will be deployed.

### Add an application descriptor

In the `manifest` directory, add `application.yaml.template` with the following 
content. 

```yaml
apiVersion: app.k8s.io/v1beta1
kind: Application
metadata:
  name: "$name"
  namespace: "$namespace"
  annotations:
    marketplace.cloud.google.com/deploy-info: '{"partner_id": "partner", "product_id": "nginx", "partner_name": "Partner"}'
  labels:
    app.kubernetes.io/name: "$name"
spec:
  descriptor:
    type: nginx
    version: '0.1.1'
  selector:
    matchLabels:
      app.kubernetes.io/name: "$name"
  componentKinds:
  # The group is determined from the apiVersion: $GROUP_NAME/$VERSION
  - group: apps
    kind: Deployment
  - group: ''
    kind: Service
```

This describes the application and is used in the GKE Applications UI.

It's important to note that `partner_id` and `product_id` must match the values 
declared in the schema, `partnerId` and `solutionId` respectively, which must also 
match your listing ID in Marketplace.

### Add the nginx manifest

In the `manifest` directory add `manifests.yaml.template`, which contains a
`service` and `deployment` definition for nginx.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $name-server
spec:
  selector:
    matchLabels:
      run: $name-app
  # Replicas was a property defined in schema.yaml. Its value will be
  # substituted into $replicas
  replicas: $replicas
  template:
    metadata:
      labels:
        run: $name-app
    spec:
      containers:
      - name: nginx-container
        image: nginx
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: $name-service
  labels:
    run: $name-app
spec:
  ports:
  - port: 80
    protocol: TCP
  selector:
    run: $name-app
```

### Build your deployer container

Create a `Dockerfile` with the following content:

```Dockerfile
FROM gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst/onbuild
```

Then you can build your container as follows:

```bash
# Set the registry to your project GCR repo.
export REGISTRY=gcr.io/$(gcloud config get-value project | tr ':' '/')
export APP_NAME=nginx

docker build --tag $REGISTRY/$APP_NAME/deployer .
```

When running `docker build`, the `deployer_envsubst/onbuild` docker container
copies the `schema.yaml` file and `manifest` directory using the `ONBUILD`
[keyword](https://docs.docker.com/engine/reference/builder/#onbuild). The
deployer container, when executed will use `envsubst` and apply the templates
in the `manifest` directory to deploy your nginx application.

Push your deployer container to the remote GCR so that your app running in your
GKE cluster can access the image:

```dockerfile
docker push $REGISTRY/$APP_NAME/deployer
```

### First deployment

Create a new namespace to cleanly deploy your app:

```shell
kubectl create namespace test-ns

mpdev install \
  --deployer=$REGISTRY/$APP_NAME/deployer \
  --parameters='{"name": "test-deployment", "namespace": "test-ns", "replicas": 3 }'
```

See [mpdev reference](mpdev-references.md), for installing the mpdev tool.

The `install` script simulates what the UI would do deploying your application.
The app parameters are specified in a JSON string and `envsubst` is used to 
substitute the parameters to the `*.template` files under the `manifest` 
directory. In the UI, the user would have configured these parameters in a form.

You can see your application in GKE UI by following this link:

```text
https://console.cloud.google.com/kubernetes/application?project=YOUR_PROJECT
```

## Part 2: Crafting the schema

`schema.yaml` is a basic JSON schema with Marketplace extensions.
See this [document](schema.md) for more references.

### Parameterize the images

Marketplace solutions must and can only use images that live on the official
`marketplace.gcr.io`. Thus **all** images used in the manifests must be
parameterized.

Each image must have a corresponding property. At deployment time, the official
images will be supplied via these properties.

In the `schema.yaml` file, the images should look like this:
```yaml
x-google-marketplace:
  schemaVersion: v2

  applicationApiVersion: v1beta1
  # The published version is required and MUST match the tag
  # of the deployer image
  publishedVersion: '0.1.1'
  publishedVersionMetadata:
    releaseNote: >-
      A first release.
  images:
    nginx:
      properties:
        nginxImage:
          type: FULL
```

The `manifests.yaml.template` file must be modified to reference `nginxImage`

```yaml
# Under spec.template
    spec:
      containers:
      - name: my-nginx
        image: $nginxImage # Changed from "nginx"
```

You __should not__ use images that are not under your control.
If your application uses some commonly available image like
`busybox`, make a copy of that image and ensure that it is free
of any vulnerability or malicious code.

Note that end users never see or need access to these default
image names.


## Parts 3 to 5

The instructions in parts 3 to 5 are not specific to the envsubst deployer.
See the
[sections](building-deployer-helm.md#part-3-crafting-application-manifest)
in the helm deployer guide
