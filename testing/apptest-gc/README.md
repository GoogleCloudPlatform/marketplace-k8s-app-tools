This sets up a CronJob in a k8s cluster to garbage collect
obsolete integration test artifacts.

The job looks for `apptest-*` namespaces that are more that
X hours old and delete them.
