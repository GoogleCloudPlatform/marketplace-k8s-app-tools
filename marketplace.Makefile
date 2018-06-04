ifndef __MARKETPLACE_MAKEFILE__

__MARKETPLACE_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile


.build/marketplace: | .build
	mkdir -p "$@"


.build/marketplace/deployer: | .build/marketplace
	mkdir -p "$@"


.build/marketplace/deployer/envsubst: \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_envsubst_base/* \
	| .build/marketplace/deployer

	$(call print_target, $@)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "gcr.io/google-marketplace-tools/k8s/deployer_envsubst" \
	      -f marketplace/deployer_envsubst_base/Dockerfile \
	      .
	@touch "$@"


.build/marketplace/deployer/helm: \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_base/* \
	| .build/marketplace/deployer

	$(call print_target, $@)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "gcr.io/google-marketplace-tools/k8s/deployer_helm" \
	      -f marketplace/deployer_helm_base/Dockerfile \
	      .
	@touch "$@"


.build/marketplace/driver: \
	$(MARKETPLACE_TOOLS_PATH)/marketplace/driver/* \
	$(MARKETPLACE_TOOLS_PATH)/scripts/* \
	| .build/marketplace

	$(call print_target, $@)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	      --tag "gcr.io/google-marketplace-tools/k8s/test_driver" \
	      -f marketplace/driver/Dockerfile \
	      .
	@touch "$@"


endif
