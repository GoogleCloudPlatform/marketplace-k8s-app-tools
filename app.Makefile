ifndef __APP_MAKEFILE__

__APP_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/base_containers.Makefile

ifdef APP_NAME
  APP_INSTANCE_NAME ?= $(APP_NAME)-1

  ifdef REGISTRY
    APP_REGISTRY ?= $(REGISTRY)/$(APP_NAME)
    APP_DEPLOYER_IMAGE ?= $(APP_REGISTRY)/deployer
  endif
endif

APP_BUILD = .build/marketplace-app

NAMESPACE ?= default

$(APP_BUILD):
	mkdir -p $(APP_BUILD)

# Using this rule as prerequisite triggers rebuilding when
# APP_REGISTRY changes.
$(APP_BUILD)/registry_prefix: $(APP_BUILD)/registry_prefix_phony ;
.PHONY: $(APP_BUILD)/registry_prefix_phony
$(APP_BUILD)/registry_prefix_phony: | $(APP_BUILD)
ifneq ($(shell [ -e "$(APP_BUILD)/registry_prefix" ] && cat "$(APP_BUILD)/registry_prefix" || echo ""),$(APP_REGISTRY))
	$(info APP_REGISTRY changed to $(APP_REGISTRY))
	@echo "$(APP_REGISTRY)" > "$(APP_BUILD)/registry_prefix"
endif

# Builds the application containers and push them to the registry.
# Including Makefile can extend this target. This target is
# a prerequisite for install.
.PHONY: app/build
app/build:: ;

# Installs the application into target namespace on the cluster.
.PHONY: app/install
app/install: app/build | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/start.sh \
	    --app-name=$(APP_NAME) \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE) \
	    --deployer=$(APP_DEPLOYER_IMAGE) \
	    --registry=$(APP_REGISTRY) \
	    --marketplace_registry=$(MARKETPLACE_REGISTRY)

# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/stop.sh \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE)

# Monitors resources in the target namespace on the cluster.
# A convenient way to look at relevant k8s resources on the CLI.
.PHONY: app/watch
app/watch: | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/watch.sh \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE)

.PHONY: app/setup
app/setup: | common/setup base/setup
ifndef APP_INSTANCE_NAME
  $(error Must define APP_INSTANCE_NAME)
endif
ifndef NAMESPACE
  $(error Must define NAMESPACE)
endif
ifndef APP_DEPLOYER_IMAGE
  $(error Must define APP_DEPLOYER_IMAGE. \
          APP_DEPLOYER_IMAGE can take a default value if APP_REGISTRY or both REGISTRY and APP_NAME are defined)
endif
ifndef APP_REGISTRY
  $(error Must define APP_REGISTRY)
endif
$(info ---- APP_INSTANCE_NAME  = $(APP_INSTANCE_NAME))
$(info ---- NAMESPACE          = $(NAMESPACE))
$(info ---- APP_DEPLOYER_IMAGE = $(APP_DEPLOYER_IMAGE))
$(info ---- APP_REGISTRY       = $(APP_REGISTRY))


endif
