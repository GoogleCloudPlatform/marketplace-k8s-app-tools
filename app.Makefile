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
$(shell echo '$(APP_PARAMETERS)' '$(APP_TEST_PARAMETERS)'
    | docker run -i --entrypoint=usr/bin/jq --rm $(APP_DEPLOYER_IMAGE) -s '.[0] * .[1]')
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
app/install: app/build \
             .build/var/MARKETPLACE_TOOLS_PATH \
             .build/var/APP_DEPLOYER_IMAGE \
             .build/var/APP_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/start.sh \
	    --namespace='$(call namespace_parameter)' \
	    --name='$(call name_parameter)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'


# Installs the application into target namespace on the cluster.
.PHONY: app/install-test
app/install-test: app/build \
                  .build/var/MARKETPLACE_TOOLS_PATH \
                  .build/var/APP_DEPLOYER_IMAGE \
                  .build/var/APP_PARAMETERS \
                  .build/var/APP_TEST_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/start.sh \
	    --namespace='$(call namespace_parameter)' \
	    --name='$(call name_parameter)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(call combined_parameters)' \
	    --entrypoint='/bin/deploy_with_tests.sh'


# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: .build/var/MARKETPLACE_TOOLS_PATH \
               .build/var/APP_DEPLOYER_IMAGE \
               .build/var/APP_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/stop.sh \
	    --namespace='$(call namespace_parameter)' \
	    --name='$(call name_parameter)'


# Runs the verification pipeline.
.PHONY: app/verify_cloudbuild
app/verify_cloudbuild: app/build \
            .build/var/MARKETPLACE_TOOLS_PATH \
            .build/var/APP_DEPLOYER_IMAGE \
            .build/var/APP_PARAMETERS \
            .build/var/APP_TEST_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/marketplace/driver/driver.sh \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --parameters='$(call combined_parameters)'

# Runs the verification pipeline.
.PHONY: app/verify
app/verify: app/build \
            .build/marketplace/driver \
            .build/var/MARKETPLACE_TOOLS_PATH \
            .build/var/APP_DEPLOYER_IMAGE \
            .build/var/APP_PARAMETERS \
            .build/var/APP_TEST_PARAMETERS
	docker run --entrypoint=/marketplace_tools/marketplace/driver/driver.sh -v \
	    /var/run/docker.sock:/var/run/docker.sock \
	    -v $(MARKETPLACE_TOOLS_PATH):/marketplace_tools \
	    -v ${HOME}/.kube/config:/.kube/config \
	    -v ${HOME}/.config/gcloud:/root/.config/gcloud \
	    --rm $(DRIVER_IMAGE) \
      --deployer='$(APP_DEPLOYER_IMAGE)' \
      --marketplace_tools='/marketplace_tools' \
      --parameters='$(call combined_parameters)'


# Monitors resources in the target namespace on the cluster.
# A convenient way to look at relevant k8s resources on the CLI.
.PHONY: app/watch
app/watch: .build/var/MARKETPLACE_TOOLS_PATH \
           .build/var/APP_DEPLOYER_IMAGE \
           .build/var/APP_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/watch.sh \
	    --namespace='$(call namespace_parameter)'


###################################################
# Placeholder targets that provide user guidance. #
###################################################

# Note: Ideally all of these targets would be marked as PHONY, but it's
# not clear how to achieve that with pattern targets.

%registry_prefix: app/phony
	@echo -e "\n\n\033[31m\033[1mThe $@ target has been replaced by .build/var/REGISTRY. Please replace */registry_prefix target with .build/var/REGISTRY.\033[0m\n\n"
	@exit 1


%tag_prefix: app/phony
	@echo -e "\n\n\033[31m\033[1mThe $@ target has been replaced by .build/var/TAG. Please replace */tag_prefix target with .build/var/TAG.\033[0m\n\n"
	@exit 1


app/setup: app/phony
	@echo -e "\n\n\033[31m\033[1mThe $@ target is deprecated. Please removed.\033[0m\n\n"
	@exit 1


endif
