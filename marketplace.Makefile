ifndef __MARKETPLACE_MAKEFILE__

__MARKETPLACE_MAKEFILE__ := included

COMMIT ?= $(shell git rev-parse HEAD | fold -w 12 | head -n 1)

makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/gcloud.Makefile
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/var.Makefile


.build/marketplace: | .build
	mkdir -p "$@"


.build/marketplace/dev: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                        $(MARKETPLACE_TOOLS_PATH)/marketplace/dev/* \
                        $(MARKETPLACE_TOOLS_PATH)/scripts/* \
                        $(MARKETPLACE_TOOLS_PATH)/marketplace.Makefile \
                        .build/var/MARKETPLACE_TOOLS_TAG \
                        | .build/marketplace
	$(call print_target)
	cd "$(MARKETPLACE_TOOLS_PATH)" ; \
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/dev/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer: | .build/marketplace
	mkdir -p "$@"


.build/marketplace/deployer/envsubst: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                                      $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_envsubst_base/* \
                                      .build/marketplace/delete_deprecated \
                                      .build/var/MARKETPLACE_TOOLS_TAG \
                                      | .build/marketplace/deployer
	$(call print_target)
	cd "$(MARKETPLACE_TOOLS_PATH)"; \
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_envsubst_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                                  $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_base/* \
                                  .build/marketplace/delete_deprecated \
                                  .build/var/COMMIT \
                                  .build/var/MARKETPLACE_TOOLS_TAG \
                                  | .build/marketplace/deployer
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	    --build-arg VERSION="$(COMMIT)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm_tiller: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                                         $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_tiller_base/* \
                                         .build/marketplace/delete_deprecated \
                                         .build/var/MARKETPLACE_TOOLS_TAG \
                                         | .build/marketplace/deployer
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_tiller_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/charts: | .build/marketplace
	mkdir -p "$@"

CHART_BUCKET = cloud-marketplace-tools-charts
MARKETPLACE_INTEGRATION_VERSION = 0.0.1
.build/marketplace/charts/marketplace-integration: \
		.build/var/CHART_BUCKET \
		.build/var/MARKETPLACE_INTEGRATION_VERSION \
		marketplace/charts/Dockerfile \
		$(shell find marketplace/charts/ -type f) \
		$(MARKETPLACE_TOOLS_PATH)/marketplace/charts/marketplace-integration/* \
		| .build/marketplace/charts
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	    --build-arg "CHART_BUCKET=$(CHART_BUCKET)" \
	    --build-arg "VERSION=$(MARKETPLACE_INTEGRATION_VERSION)" \
	    -f marketplace/charts/Dockerfile \
	    marketplace/charts
	@touch $@


.build/marketplace/delete_deprecated: | .build/marketplace
# For BSD compatibility, we can't use xargs -r.
	@ \
	for image in $$(docker images --format '{{.Repository}}' \
	    | sort | uniq \
	    | grep 'gcr.io/google-marketplace-tools/'); do \
	  printf "\n\033[93m\033[1m$${image} is DEPRECATED. Please update your Dockerfile\033[0m\n\n"; \
	done
	@ \
	for image in $$(docker images --format '{{.Repository}}:{{.Tag}}' \
	    | grep 'gcr.io/google-marketplace-tools/' \
	    | grep -v -e '<[Nn]one>'); do \
	  docker rmi "$${image}"; \
	done
	@touch "$@"


endif
