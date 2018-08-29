ifndef __APP_MAKEFILE__

__APP_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/var.Makefile


# Extracts the name property from APP_PARAMETERS.
define name_parameter
$(shell echo '$(APP_PARAMETERS)' \
    | docker run -i --entrypoint=/bin/print_config.py --rm $(APP_DEPLOYER_IMAGE) --values_file=- --param '{"x-google-marketplace": {"type": "NAME"}}')
endef


# Extracts the namespace property from APP_PARAMETERS.
define namespace_parameter
$(shell echo '$(APP_PARAMETERS)' \
    | docker run -i --entrypoint=/bin/print_config.py --rm $(APP_DEPLOYER_IMAGE) --values_file=- --param '{"x-google-marketplace": {"type": "NAMESPACE"}}')
endef


# Combines APP_PARAMETERS and APP_TEST_PARAMETERS.
define combined_parameters
$(shell echo '$(APP_PARAMETERS)' '$(APP_TEST_PARAMETERS)' \
    | docker run -i --entrypoint=/usr/bin/jq --rm $(APP_DEPLOYER_IMAGE) -s '.[0] * .[1]')
endef

KUBE_CONFIG ?= $(HOME)/.kube
GCLOUD_CONFIG ?= $(HOME)/.config/gcloud
EXTRA_DOCKER_PARAMS ?=

.build/app: | .build
	mkdir -p "$@"


.PHONY: app/phony
app/phony: ;


# Builds the application containers and push them to the registry.
# Including Makefile can extend this target. This target is
# a prerequisite for install.
.PHONY: app/build
app/build:: ;


# Installs the application into target namespace on the cluster.
.PHONY: app/install
app/install:: app/build \
              .build/var/APP_DEPLOYER_IMAGE \
              .build/var/APP_PARAMETERS \
              .build/var/HOME \
              .build/var/MARKETPLACE_TOOLS_TAG
	$(call print_target)
	docker run \
	    --mount "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,readonly" \
	    --mount "type=bind,source=$(KUBE_CONFIG),target=/root/mount/.kube,readonly" \
	    --mount "type=bind,source=$(GCLOUD_CONFIG),target=/root/mount/.config/gcloud,readonly" \
	    $(EXTRA_DOCKER_PARAMS) \
	    --rm \
	    "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    -- \
	    /scripts/install \
	          --deployer='$(APP_DEPLOYER_IMAGE)' \
	          --parameters='$(APP_PARAMETERS)' \
	          --entrypoint="/bin/deploy.sh"


# Installs the application into target namespace on the cluster.
.PHONY: app/install-test
app/install-test:: app/build \
                   .build/var/APP_DEPLOYER_IMAGE \
                   .build/var/APP_PARAMETERS \
                   .build/var/APP_TEST_PARAMETERS \
                   .build/var/HOME \
                   .build/var/MARKETPLACE_TOOLS_TAG
	$(call print_target)
	docker run \
	    --mount "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,readonly" \
	    --mount "type=bind,source=$(KUBE_CONFIG),target=/root/mount/.kube,readonly" \
	    --mount "type=bind,source=$(GCLOUD_CONFIG),target=/root/mount/.config/gcloud,readonly" \
	    $(EXTRA_DOCKER_PARAMS) \
	    --rm \
	    "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    -- \
	    /scripts/install \
	          --deployer='$(APP_DEPLOYER_IMAGE)' \
	          --parameters='$(call combined_parameters)' \
	          --entrypoint="/bin/deploy_with_tests.sh"


# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: .build/var/APP_DEPLOYER_IMAGE \
               .build/var/APP_PARAMETERS
	$(call print_target)
	kubectl delete 'application/$(call name_parameter)' \
	    --namespace='$(call namespace_parameter)' \
	    --ignore-not-found


# Runs the verification pipeline.
.PHONY: app/verify
app/verify: app/build \
            .build/var/APP_DEPLOYER_IMAGE \
            .build/var/APP_PARAMETERS \
            .build/var/APP_TEST_PARAMETERS \
            .build/var/HOME \
            .build/var/MARKETPLACE_TOOLS_TAG
	$(call print_target)
	docker run \
	    --mount "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,readonly" \
	    --mount "type=bind,source=$(KUBE_CONFIG),target=/root/mount/.kube,readonly" \
	    --mount "type=bind,source=$(GCLOUD_CONFIG),target=/root/mount/.config/gcloud,readonly" \
	    $(EXTRA_DOCKER_PARAMS) \
	    --rm \
	    "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    -- \
	    /scripts/verify \
	          --deployer='$(APP_DEPLOYER_IMAGE)' \
	          --parameters='$(call combined_parameters)'


endif
