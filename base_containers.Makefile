ifndef __BASE_CONTAINERS_MAKEFILE__

__BASE_CONTAINERS_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/var.Makefile

.build/base:
	mkdir -p "$@"


.build/base/deployer: | .build/base
	mkdir -p "$@"


.build/base/deployer/envsubst: \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_kubectl_base/* \
	| base/setup .build/base/deployer

	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "gcr.io/google-marketplace-tools/k8s/deployer_envsubst" \
	      -f marketplace/deployer_kubectl_base/Dockerfile \
	      .
	@touch "$@"


.build/base/deployer/helm: \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_base/* \
	| base/setup .build/base/deployer

	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "gcr.io/google-marketplace-tools/k8s/deployer_helm" \
	      -f marketplace/deployer_helm_base/Dockerfile \
	      .
	@touch "$@"


.build/base/driver: \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/driver/* \
	$(MARKETPLACE_TOOLS_PATH)/scripts/* \
	| base/setup

	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "gcr.io/google-marketplace-tools/k8s/test_driver" \
	      -f marketplace/driver/Dockerfile \
	      .
	@touch "$@"


.PHONY: base/setup
base/setup: | common/setup .build/base


endif
