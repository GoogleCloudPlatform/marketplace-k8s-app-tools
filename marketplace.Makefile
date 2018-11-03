ifndef __MARKETPLACE_MAKEFILE__

__MARKETPLACE_MAKEFILE__ := included

COMMIT ?= $(shell git rev-parse HEAD | fold -w 12 | head -n 1)

include common.Makefile
include var.Makefile


.build/marketplace: | .build
	mkdir -p "$@"


.build/marketplace/dev: marketplace/deployer_util/* \
                        marketplace/dev/* \
                        scripts/* \
                        marketplace.Makefile \
                        .build/var/MARKETPLACE_TOOLS_TAG \
                        | .build/marketplace
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/dev/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer: | .build/marketplace
	mkdir -p "$@"


.build/marketplace/deployer/envsubst: marketplace/deployer_util/* \
                                      marketplace/deployer_envsubst_base/* \
                                      .build/marketplace/delete_deprecated \
                                      .build/var/MARKETPLACE_TOOLS_TAG \
                                      | .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_envsubst_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm: marketplace/deployer_util/* \
                                  marketplace/deployer_helm_base/* \
                                  .build/marketplace/delete_deprecated \
                                  .build/var/COMMIT \
                                  .build/var/MARKETPLACE_TOOLS_TAG \
                                  | .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --build-arg VERSION="$(COMMIT)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm_tiller: \
		.build/var/MARKETPLACE_TOOLS_TAG \
		marketplace/deployer_helm_tiller_base/* \
		marketplace/deployer_util/* \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_tiller_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm_tiller_onbuild: \
		.build/marketplace/deployer/helm_tiller \
		.build/var/MARKETPLACE_TOOLS_TAG \
		marketplace/deployer_helm_tiller_base/onbuild/* \
		marketplace/deployer_util/* \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --build-arg FROM="gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$(MARKETPLACE_TOOLS_TAG)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller/onbuild:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_tiller_base/onbuild/Dockerfile \
	    .
	@touch "$@"


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
