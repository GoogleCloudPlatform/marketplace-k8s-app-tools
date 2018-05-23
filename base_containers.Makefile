ifndef __BASE_CONTAINERS_MAKEFILE__

dependon=$(shell find $1 -type f | sed -e 's/ /\\ /g')

__BASE_CONTAINERS_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile

MARKETPLACE_BASE_BUILD = .build/marketplace-base-containers

ifdef REGISTRY
  MARKETPLACE_REGISTRY ?= $(REGISTRY)/marketplace
endif

$(MARKETPLACE_BASE_BUILD):
	mkdir -p $(MARKETPLACE_BASE_BUILD)

# Target for invoking directly with make. Don't use this as a prerequisite
# if your target needs to build kubectl deployer.
# Use $(MARKETPLACE_BASE_BUILD)/deployer-kubectl instead.
.PHONY: base/build/deployer/kubectl
base/build/deployer/kubectl: $(MARKETPLACE_BASE_BUILD)/deployer-kubectl ;

$(MARKETPLACE_BASE_BUILD)/deployer-kubectl: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_kubectl_base/* $(MARKETPLACE_BASE_BUILD)/registry_prefix | base/setup
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "$(MARKETPLACE_REGISTRY)/deployer_kubectl_base" \
	      -f marketplace/deployer_kubectl_base/Dockerfile \
	      .
	gcloud docker -- push "$(MARKETPLACE_REGISTRY)/deployer_kubectl_base"
	@touch "$@"

# Target for invoking directly with make. Don't use this as a prerequisite
# if your target needs to build helm deployer.
# Use $(MARKETPLACE_BASE_BUILD)/deployer-helm instead.
.PHONY: base/build/deployer/helm
base/build/deployer/helm: $(MARKETPLACE_BASE_BUILD)/deployer-helm ;

$(MARKETPLACE_BASE_BUILD)/deployer-helm: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_base/* $(MARKETPLACE_BASE_BUILD)/registry_prefix | base/setup
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "$(MARKETPLACE_REGISTRY)/deployer_helm_base" \
	      -f marketplace/deployer_helm_base/Dockerfile \
	      .
	gcloud docker -- push "$(MARKETPLACE_REGISTRY)/deployer_helm_base"
	@touch "$@"

# Target for invoking directly with make. Don't use this as a prerequisite
# if your target needs to build the driver.
# Use $(MARKETPLACE_BASE_BUILD)/driver instead.
.PHONY: base/build/driver
base/build/driver: $(MARKETPLACE_BASE_BUILD)/driver ;

$(MARKETPLACE_BASE_BUILD)/driver: \
	$(MARKETPLACE_BASE_BUILD)/registry_prefix \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/driver/* \
	$(MARKETPLACE_TOOLS_PATH)/scripts/* \
	| base/setup
	
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "$(MARKETPLACE_REGISTRY)/driver" \
	      -f marketplace/driver/Dockerfile \
	      .
	gcloud docker -- push "$(MARKETPLACE_REGISTRY)/driver"
	@touch "$@"

.PHONY: base/build/testrunner
base/build/testrunner: $(MARKETPLACE_BASE_BUILD)/testrunner ;

$(MARKETPLACE_BASE_BUILD)/testrunner: $(call dependon, $(MARKETPLACE_TOOLS_PATH)/testrunner/)
	cd $(MARKETPLACE_TOOLS_PATH)/testrunner \
	&& bazel run //runner:go_image -- --norun \
	&& docker tag bazel/runner:go_image gcr.io/$(REGISTRY)/testrunner
	@touch "$@"

# Using this rule as a prerequisite triggers rebuilding when
# MARKETPLACE_REGISTRY variable changes its value.
$(MARKETPLACE_BASE_BUILD)/registry_prefix: $(MARKETPLACE_BASE_BUILD)/registry_prefix_phony ;

.PHONY: $(MARKETPLACE_BASE_BUILD)/registry_prefix_phony
$(MARKETPLACE_BASE_BUILD)/registry_prefix_phony: | $(MARKETPLACE_BASE_BUILD)
ifneq ($(shell [ -e "$(MARKETPLACE_BASE_BUILD)/registry_prefix" ] && cat "$(MARKETPLACE_BASE_BUILD)/registry_prefix" || echo ""),$(MARKETPLACE_REGISTRY))
	$(info MARKETPLACE_REGISTRY changed to $(MARKETPLACE_REGISTRY))
	@echo "$(MARKETPLACE_REGISTRY)" > "$(MARKETPLACE_BASE_BUILD)/registry_prefix"
endif

.PHONY: base/setup
base/setup: | common/setup $(MARKETPLACE_BASE_BUILD)
ifndef MARKETPLACE_REGISTRY
	$(error Must define MARKETPLACE_REGISTRY);
endif
	$(info ---- MARKETPLACE_REGISTRY = $(MARKETPLACE_REGISTRY))


endif
