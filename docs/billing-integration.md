# Billing Integration

## Overview

This guide provides an overview of billing integration for Kubernetes applications in
GCP Marketplace.

## See Also

* [Choosing a pricing model](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/select-pricing)
* [Requirements to integrate the billing agent](https://cloud.google.com/marketplace/docs/partners/kubernetes-solutions/create-app-package#billing-agent)

## Usage Reporting

Kubernetes apps that bill a Google Cloud customer's account must report usage to Google. Ultimately these usage reports must be sent to [Google Service Control](https://cloud.google.com/service-infrastructure/docs/service-control/reference/rest/), but Marketplace provides a [metering agent](https://github.com/GoogleCloudPlatform/ubbagent) to simplify this integration. All metrics used for commercial billing must be reported by the application, including simple metrics such the amount of time the application has been running.

Usage reporting requires the following information:
* Predefined usage metrics. These metrics (such as `requests` or `instance_time`) are defined when choosing a pricing model. Usage for these metrics must be reported from your deployed application.
* A service name. This name identifies your product and will look like `my-application.mp-my-company.appspot.com`. It will be provided by Google during onboarding.
* A GCP service account key to use for reporting. This will be provided to your application at deployment time.
* A consumer ID. This will be provided to your application at deployment time.

## The Reporting `secret` Resource

During the deployment of a Kubernetes app, GCP Marketplace will create a `secret` resource containing the **service account key** and **consumer ID** referenced above. The exact name of the created resource will be passed to your application via a  parameter defined in [schema.yaml](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/schema.md) with the special `REPORTING_SECRET` annotation.

For example, the following `schema.yaml` snippet results in a property named `$myReportingSecret` being populated with the name of the generated secret resource.
```yaml
applicationApiVersion: v1beta1
properties:
  myReportingSecret:
    type: string
    x-google-marketplace:
      type: REPORTING_SECRET
  ...
```

**Note:** A reporting secret will generally look like `{deployment-name}-reporting-secret`, where `{deployment-name}` is the name given to the application deployment by the customer.

The reporting secret contains the following three fields (see an [example](https://storage.cloud.google.com/cloud-marketplace-tools/reporting_secrets/fake_reporting_secret.yaml)):
* **consumer-id** - an identifier that represents the customer being billed for usage. To be passed verbatim to Google Service Control.
* **entitlement-id** - another identifier representing the customer, but generally unused.
* **reporting-key** - a base64-encoded GCP JSON service account key to use when reporting usage.

**Note:** when viewing the YAML representation of this secret, every field is base64-encoded and will be automatically decoded by Kubernetes when reading values. The **reporting-key** field is encoded an additional time, so your application will need to decode it (after it is automatically decoded by Kubernetes once) if it needs to read the actual JSON key data.

## Using the Metering Agent

You can choose to use the Marketplace-provided [metering agent](https://github.com/GoogleCloudPlatform/ubbagent) to simplify usage reporting. The metering agent can be included into your Kubernetes deployment as a sidecar container, included in your own container, or built directly into your application if it's written in Go. Including the agent as a sidecar is the most straightforward.

The metering agent is configured with usage reporting credentials, the metrics that will be reported, and the report destination. Much of the configuration is boilerplate, and you'll need to only update some identifiers related to your application.

If your application is priced by usage time (how long a deployment runs), you can configure the agent to report automatically. For anything else your application will need to report usage to the agent either periodically or as it occurs. When deployed as a sidecar, the metering agent listens on the loopback interface (127.0.0.1), and is only reachable by other containers in the same pod.

**Note:** the metering agent's HTTP interface is unencrypted and unauthenticated, and works under the assumption that access is limited to containers within the same pod.

### Agent Deployment and Configuration

The following excerpts include the metering agent as a sidecar along with some application container. The agent's configuration is included as a ConfigMap value. When deployed as a sidecar, the agent's configuration can be parameterized through the use of environment variables, which is the mechanism used for passing values from the reporting secret.

Kubernetes manifest excerpt:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: $name-ubbagent-config
data:
  config.yaml: |
    # The identity section contains authentication information used
    # by the agent.
    identities:
    - name: gcp
      gcp:
        # This parameter accepts a base64-encoded JSON service
        # account key. The value comes from the reporting secret.
        encodedServiceAccountKey: $AGENT_ENCODED_KEY

    # The metrics section defines the metric that will be reported.
    # Metric names should match verbatim the identifiers created
    # during pricing setup.
    metrics:
    - name: requests
      type: int

      # The endpoints section of a metric defines which endpoints the
      # metric data is sent to.
      endpoints:
      - name: on_disk
      - name: servicecontrol

      # The aggregation section indicates that reports that the agent
      # receives for this metric should be aggregated for a specified
      # period of time prior to being sent to the reporting endpoint.
      aggregation:
        bufferSeconds: 60

    - name: instance_time
      type: int
      endpoints:
      - name: on_disk
      - name: servicecontrol

      # The passthrough marker indicates that no aggregation should
      # occur for this metric. Reports received are immediately sent
      # to the reporting endpoint. We use passthrough for the
      # instance_time metric since reports are generated
      # automatically by a heartbeat source defined in a later
      # section.
      passthrough: {}

    # The endpoints section defines where metering data is ultimately
    # sent. Currently supported endpoints include:
    # * disk - some directory on the local filesystem
    # * servicecontrol - Google Service Control
    endpoints:
    - name: on_disk
      # The disk endpoint is useful for debugging, but its inclusion
      # is not necessary in a production deployment.
      disk:
        reportDir: /var/lib/ubbagent/reports
        expireSeconds: 3600
    - name: servicecontrol
      servicecontrol:
        identity: gcp
        # The service name is unique to your application and will be
        # provided during onboarding.
        serviceName: my-application.mp-my-company.appspot.com
        consumerId: $AGENT_CONSUMER_ID  # From the reporting secret.
      

    # The sources section lists metric data sources run by the agent
    # itself. The currently-supported source is 'heartbeat', which
    # sends a defined value to a metric at a defined interval. In
    # this example, the heartbeat sends a 60-second value through the
    # "instance_time" metric every minute.
    sources:
    - name: instance_time_heartbeat
      heartbeat:
        metric: instance_time
        intervalSeconds: 60
        value:
          int64Value: 60
---
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: $name-metered-app
  labels: &AppDeploymentLabels
    app.kubernetes.io/name: "$name"
    app.kubernetes.io/component: my-application
spec:
  replicas: 1
  selector:
    matchLabels: *AppDeploymentLabels
  template:
    metadata:
      labels: *AppDeploymentLabels
    spec:
      containers:
      - name: my-app
        image: $imageMyApp
        # ... your app container's config ...
      - name: ubbagent
        image: $imageUbbagent
        env:
        - name: AGENT_CONFIG_FILE
          value: "/etc/ubbagent/config.yaml"
        - name: AGENT_LOCAL_PORT
          value: "4567"
        - name: AGENT_ENCODED_KEY
          valueFrom:
            secretKeyRef:
              name: $reportingSecret
              key: reporting-key
        - name: AGENT_CONSUMER_ID
          valueFrom:
            secretKeyRef:
              name: $reportingSecret
              key: consumer-id
        volumeMounts:
        - name: ubbagent-config
          mountPath: /etc/ubbagent
      volumes:
      - name: ubbagent-config
        configMap:
          name: ubbagent-config
```

`schema.yaml` excerpt:
```yaml
application_api_version: v1beta1
properties:
  name:
    type: string
    x-google-marketplace:
      type: NAME
  imageMyApp:
    type: string
    default: $REGISTRY:$TAG
    x-google-marketplace:
      type: IMAGE
  imageUbbagent:
    type: string
    default: $REGISTRY/ubbagent:$TAG
    x-google-marketplace:
      type: IMAGE
  reportingSecret:
    type: string
    x-google-marketplace:
      type: REPORTING_SECRET
```

The important aspects of the above examples include:
* The metering agent's config is included as a value named `config.yaml` within a config-map.
* This config-map is mounted as a volume at `/etc/ubbagent` in the ubbagent container, making the config file available to the agent at `/etc/ubbagent/config.yaml`. This value is passed to the agent sidecar using the special `$AGENT_CONFIG_FILE` environment variable.
* The agent is instructed to listen on port `4567` using the special `$AGENT_LOCAL_PORT` environment variable. Note that this value must be quoted since environment variable values must be strings.
* The name of the reported secret created at deployment time is stored in the `$reportingSecret` parameter.
* The `config.yaml` file references two additional environment variables, `$AGENT_ENCODED_KEY` and `$AGENT_CONSUMER_ID`. The values for these variables are piped through from the above reporting secret using `secretKeyRef` sections. Note that the `AGENT_ENCODED_KEY` and `AGENT_CONSUMER_ID` names aren't special; any valid environment variable names can be used as long as they're consistent in the agent configuration and `env` sections.

With this configuration in place, the application can send usage reports to the agent at `http://localhost:4567`.

**Note:** Use of the `$AGENT_ENCODED_KEY` and `$AGENT_CONSUMER_ID` variables in the previous example rely on variable expansion provided by the ubbagent sidecar container. The mechanism isn't supported natively by the agent. If you're using the agent in a manner other than the sidecar, you can still use the environment variable technique described above but will need to paramaterize the configuration using some other mechanism.

### Sending Usage Reports

Reports are sent to the agent over a simple http interface. Each report contains a value for a single metric. The following example script sends a report for a single request.
```shell
$ read -d '' REPORT <<EOF
{
  "name": "requests",
  "startTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "endTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "value": { "int64Value": 1 }
}
EOF
$ curl -X POST -d "$REPORT" 'http://localhost:4567/report'
```

For one-shot requests like this, the start and end times can be equal. For a report that spans a longer period of time, you should set the start and end times to cover time span.

### Monitoring Status

Your app can monitor the metering agent's status and modify its behavior if usage reports begin to fail. For example:
```shell
$ curl 'http://localhost:4567/status'
{
  "lastReportSuccess": "2019-04-01T12:06:32Z",
  "currentFailureCount": 3,
  "totalFailureCount": 10
}
```

The `currentFailureCount` value is the number of failures since the last successful report, and will be reset to 0 the next time a report is successfully sent. The `totalFailureCount` is the total number of failures since the agent started.

### Monitoring Logs

When the metering agent is deployed as a sidecar, you can inspect its container log output for useful messages including:
* when reports are received
* when reports are sent to Google
* the success or failure of reports sent to Google

Additionally, if you've configured a `disk` endpoint, you can inspect the contents of the configured output directory to ensure that aggregated report values are as you'd expect.

### Getting a Reporting Secret for Testing

There's currently no way to create a valid reporting secret for your application until it's published in GCP Marketplace (it doesn't need to be published publicly). You can use [this](https://storage.cloud.google.com/cloud-marketplace-tools/reporting_secrets/fake_reporting_secret.yaml) fake secret file which is structurally correct, but will fail authentication. Use the following procedure to get a valid secret for testing:

* Once pricing has been submitted and published, submit and have published an initial version of your app. This version does not need to have working metering configuration, but should include the `REPORTING_SECRET` entry in schema.yaml.
* Deploy your application to a cluster.
* Once deployed, read the reporting secret installed into the cluster and use it for additional local testing. For example:
```shell
$ kubectl get secret "my-app-reporting-secret" -n my-namespace --output json
```
