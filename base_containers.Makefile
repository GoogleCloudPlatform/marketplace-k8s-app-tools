ifndef __BASE_CONTAINERS_MAKEFILE__

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

$(MARKETPLACE_BASE_BUILD)/deployer-kubectl: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_kubectl_base/* gcloud/REGISTRY | base/setup
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

$(MARKETPLACE_BASE_BUILD)/deployer-helm: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_base/* gcloud/REGISTRY | base/setup
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
	gcloud/REGISTRY \
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

.PHONY: base/setup
base/setup: | common/setup $(MARKETPLACE_BASE_BUILD)
ifndef MARKETPLACE_REGISTRY
	$(error Must define MARKETPLACE_REGISTRY);
endif
	$(info ---- MARKETPLACE_REGISTRY = $(MARKETPLACE_REGISTRY))


endif
