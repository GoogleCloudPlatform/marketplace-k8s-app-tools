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

required:
- name
- namespace
- replicas
```


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
  - group: ''
    kind: Deployment
  - group: ''
    kind: Service
```

This describes the application and is used in the GKE Applications UI.

It's important to note that partner_id and product_id must match the values 
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
      run: my-nginx
  replicas: $replicas
  template:
    metadata:
      labels:
        run: my-nginx
    spec:
      containers:
      - name: my-nginx
        image: nginx
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: my-nginx
  labels:
    run: my-nginx
spec:
  ports:
  - port: 80
    protocol: TCP
  selector:
    run: my-nginx
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

Push your built container to the remote GCR so that your app running in your GKE
cluster can access the image:

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
# Under the x-google-marketplace parent attribute  
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
