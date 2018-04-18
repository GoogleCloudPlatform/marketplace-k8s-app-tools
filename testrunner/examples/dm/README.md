This directory containers example Deployment Manager templates.
The ones ending with `_test` are what you want to create deployments
out of. For example:

```shell
gcloud deployment-manager deployments create my-deployment --template spec_passing_test.jinja
```
