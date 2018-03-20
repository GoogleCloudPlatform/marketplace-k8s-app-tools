ifndef __APP_MAKEFILE__

__APP_MAKEFILE__ := included


include $(dir $(realpath $(lastword $(MAKEFILE_LIST))))/common.Makefile
include $(dir $(realpath $(lastword $(MAKEFILE_LIST))))/base_containers.Makefile

ifdef APP_NAME
  APP_INSTANCE_NAME ?= $(APP_NAME)-1

  ifdef REGISTRY
    APP_REGISTRY ?= $(REGISTRY)/$(APP_NAME)
    APP_DEPLOYER_IMAGE ?= $(APP_REGISTRY)/deployer
  endif
endif

NAMESPACE ?= default

.PHONY: app/build
app/build:: ;

.PHONY: app/install
app/install: app/build | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/start.sh \
	    --app-name=$(APP_NAME) \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE) \
	    --deployer=$(APP_DEPLOYER_IMAGE) \
	    --registry=$(APP_REGISTRY) \
	    --marketplace_registry=$(MARKETPLACE_REGISTRY)

.PHONY: app/delete
app/delete: | app/setup
	$(MARKETPLACE_TOOLS_PATH)/scripts/stop.sh \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE)

.PHONY: app/uninstall
app/uninstall: app/delete

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
