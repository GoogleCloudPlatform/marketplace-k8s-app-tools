# Annotation
## Requirement
Starting January 20, 2025, new and updated container images associated with a Marketplace Container Registry image and Google Kubernetes Engine listing must include the following [annotation](https://github.com/opencontainers/image-spec/blob/main/annotations.md) in their [image manifest](https://github.com/opencontainers/image-spec/blob/main/manifest.md):

```
com.googleapis.cloudmarketplace.product.service.name=<Product Service Name>
```
Example:
```
com.googleapis.cloudmarketplace.product.service.name=services/example.com
```

## How to Add annotations
The key for the annotation is `com.googleapis.cloudmarketplace.product.service.name`, and the value is your product's associated service management service name.  

You can add this annotation to your images using several method:


* **Add annotations at build time**:
Add annotations to an image at build time, or when creating the image manifest. Refer to the [Docker doc](https://docs.docker.com/build/metadata/annotations/#add-annotations) for instructions.
* **Add annotations with the [crane tool](https://github.com/google/go-containerregistry/blob/main/cmd/crane/doc/crane.md)**: The crane tool provides a convenient way to modify existing images. Use the mutate command with the --annotation flag to add the required annotation.

Example:
```
crane mutate --annotation com.googleapis.cloudmarketplace.product.service.name=<product service name> <image uri>
```

### Find Product Service Name
You can find the Service name for your products in the products table, located on your [Producer Portal’s Overview page](https://cloud.google.com/marketplace/docs/partners/integrated-saas/set-up-environment#start-creating-solution). Prefix the service name with `services/`.

Example:
```
services/example.endpoints.myproject.cloud.goog
```