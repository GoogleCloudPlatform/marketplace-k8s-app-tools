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
              .build/var/MARKETPLACE_TOOLS_PATH
	$(call print_target)
	docker run \
	    --volume "/var/run/docker.sock:/var/run/docker.sock:ro" \
	    --volume "$(HOME)/.kube:/root/mount/.kube:ro" \
	    --volume "$(HOME).config/gcloud:/root/mount/.config/gcloud:ro" \
	    --rm \
	    "gcr.io/cloud-marketplace-tools/k8s/dev" \
	    -- \
	    /scripts/install \
	          --deployer="$(APP_DEPLOYER_IMAGE)" \
	          --parameters="$(APP_PARAMETERS)" \
	          --entrypoint="/bin/deploy.sh"


# Installs the application into target namespace on the cluster.
.PHONY: app/install-test
app/install-test:: app/build \
                   .build/var/MARKETPLACE_TOOLS_PATH \
                   .build/var/APP_DEPLOYER_IMAGE \
                   .build/var/APP_PARAMETERS \
                   .build/var/APP_TEST_PARAMETERS \
                   .build/var/HOME \
	$(call print_target)
	docker run \
	    --volume "/var/run/docker.sock:/var/run/docker.sock:ro" \
	    --volume "$(HOME)/.kube:/root/mount/.kube:ro" \
	    --volume "$(HOME).config/gcloud:/root/mount/.config/gcloud:ro" \
	    --rm \
	    "gcr.io/cloud-marketplace-tools/k8s/dev" \
	    -- \
	    /scripts/install \
	          --deployer="$(APP_DEPLOYER_IMAGE)" \
	          --parameters="$(call combined_parameters)" \
	          --entrypoint="/bin/deploy_with_tests.sh"


# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: .build/var/APP_DEPLOYER_IMAGE \
               .build/var/APP_PARAMETERS \
               .build/var/MARKETPLACE_TOOLS_PATH
	$(call print_target)
	kubectl delete 'application/$(call name_parameter)' \
	    --namespace='$(call namespace_parameter)' \
	    --ignore-not-found


# Runs the verification pipeline.
.PHONY: app/verify
app/verify: app/build \
            .build/var/MARKETPLACE_TOOLS_PATH \
            .build/var/HOME \
            .build/var/APP_DEPLOYER_IMAGE \
            .build/var/APP_PARAMETERS \
            .build/var/APP_TEST_PARAMETERS
	$(call print_target)
	docker run \
	    --volume "/var/run/docker.sock:/var/run/docker.sock:ro" \
	    --volume "$(HOME)/.kube:/root/mount/.kube:ro" \
	    --volume "$(HOME).config/gcloud:/root/mount/.config/gcloud:ro" \
	    --rm -it \
	    "gcr.io/cloud-marketplace-tools/k8s/dev" \
	    -- \
	    /scripts/verify \
	          --deployer='$(APP_DEPLOYER_IMAGE)' \
	          --parameters='$(call combined_parameters)'

endif
