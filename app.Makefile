ifndef __APP_MAKEFILE__

__APP_MAKEFILE__ := included

makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/base_containers.Makefile

.build/marketplace-app:
	mkdir -p .build/marketplace-app

# Builds the application containers and push them to the registry.
# Including Makefile can extend this target. This target is
# a prerequisite for install.
.PHONY: app/build
app/build:: ;

# Builds the application containers in test mode and push them to the registry.
# Including Makefile can extend this target. This target is
# a prerequisite for install-test.
.PHONY: app/build-test
app/build-test:: ;

# Installs the application into target namespace on the cluster.
.PHONY: app/install
app/install: app/build \
             assert-var-MARKETPLACE_TOOLS_PATH \
             assert-var-APP_DEPLOYER_IMAGE \
             assert-var-APP_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/start.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'

# Installs the application into target namespace on the cluster.
.PHONY: app/install-test
app/install-test: app/build-test \
                  assert-var-MARKETPLACE_TOOLS_PATH \
                  assert-var-APP_DEPLOYER_IMAGE \
                  assert-var-APP_PARAMETERS \
                  assert-var-APP_TEST_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/start_test.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)' \
	    --test_parameters='$(APP_TEST_PARAMETERS)'

# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: assert-var-MARKETPLACE_TOOLS_PATH \
               assert-var-APP_DEPLOYER_IMAGE \
               assert-var-APP_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/stop.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'

# Runs the verification pipeline.
.PHONY: app/verify
app/verify: app/build app/build-test \
            assert-var-MARKETPLACE_TOOLS_PATH \
            assert-var-APP_DEPLOYER_IMAGE \
            assert-var-APP_PARAMETERS \
            assert-var-APP_TEST_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/marketplace/driver/driver.sh \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --parameters='$(APP_PARAMETERS)' \
	    --test_parameters='$(APP_TEST_PARAMETERS)'

# Monitors resources in the target namespace on the cluster.
# A convenient way to look at relevant k8s resources on the CLI.
.PHONY: app/watch
app/watch: assert-var-MARKETPLACE_TOOLS_PATH \
           assert-var-APP_DEPLOYER_IMAGE \
           assert-var-APP_PARAMETERS
	$(MARKETPLACE_TOOLS_PATH)/scripts/watch.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'

###################################################
# Placeholder targets that provide user guidance. #
###################################################

# Note: Ideally all of these targets would be marked as PHONY, but it's
# not clear how to achieve that with pattern targets.
.PHONY: /registry_prefix /tag_prefix app/setup registry_prefix_phony tag_prefix_phony

/registry_prefix:
	@echo "\n\n\033[31m\033[1mThe $@ target has been replaced by .build/var/REGISTRY. Please replace */registry_prefix target with .build/var/REGISTRY.\033[0m\n\n"
	@exit 1

registry_prefix_phony: ;
%/registry_prefix: registry_prefix_phony
	@echo -e "\n\n\033[31m\033[1mThe $@ target has been replaced by .build/var/REGISTRY. Please replace */registry_prefix target with .build/var/REGISTRY.\033[0m\n\n"
	@exit 1

/tag_prefix:
	@echo -e "\n\n\033[31m\033[1mThe $@ target has been replaced by .build/var/TAG. Please replace */tag_prefix target with .build/var/TAG.\033[0m\n\n"
	@exit 1

tag_prefix_phony: ;
%/tag_prefix: tag_prefix_phony
	@echo -e "\n\n\033[31m\033[1mThe $@ target has been replaced by .build/var/TAG. Please replace */tag_prefix target with .build/var/TAG.\033[0m\n\n"
	@exit 1

app/setup:
	@echo -e "\n\n\033[31m\033[1mThe $@ target is deprecated. Please removed.\033[0m\n\n"
	@exit 1

endif
