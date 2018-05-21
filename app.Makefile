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
app/install: app/build | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/start.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'

# Installs the application into target namespace on the cluster.
.PHONY: app/install-test
app/install-test: app/build-test | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/start_test.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)' \
	    --test_parameters='$(APP_TEST_PARAMETERS)'

# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/stop.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'

# Runs the verification pipeline.
.PHONY: app/verify
app/verify: app/build app/build-test | app/setup
	$(MARKETPLACE_TOOLS_PATH)/marketplace/driver/driver.sh \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --parameters='$(APP_PARAMETERS)' \
	    --test_parameters='$(APP_TEST_PARAMETERS)'

# Monitors resources in the target namespace on the cluster.
# A convenient way to look at relevant k8s resources on the CLI.
.PHONY: app/watch
app/watch: | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/watch.sh \
	    --marketplace_tools='$(MARKETPLACE_TOOLS_PATH)' \
	    --deployer='$(APP_DEPLOYER_IMAGE)' \
	    --parameters='$(APP_PARAMETERS)'

.PHONY: app/setup
app/setup: | base/setup .build/marketplace-app
ifndef APP_DEPLOYER_IMAGE
	$(error must set APP_DEPLOYER_IMAGE variable)
endif
ifndef APP_PARAMETERS
	$(error must set APP_PARAMETERS variable)
endif
ifndef APP_TEST_PARAMETERS
	# TODO(https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/issues/102):
	# APP_TEST_PARAMETERS should not cause failures for make
	# app/install.
	$(error must set APP_TEST_PARAMETERS variable)
endif

	$(info ---- )
	$(info ---- APP_DEPLOYER_IMAGE  = $(APP_DEPLOYER_IMAGE))
	$(info ---- )
	$(info ---- APP_PARAMETERS      = $(APP_PARAMETERS))
	$(info ---- )
	$(info ---- APP_TEST_PARAMETERS = $(APP_TEST_PARAMETERS))
	$(info ---- )

	@ [ -n "$$(which jq)" ] || (echo 'Please install jq.'; exit 1)

endif
