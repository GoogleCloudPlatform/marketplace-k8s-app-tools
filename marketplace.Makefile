ifndef __MARKETPLACE_MAKEFILE__

__MARKETPLACE_MAKEFILE__ := included


include common.Makefile
include var.Makefile


marketplace/build: .build/marketplace/dev \
                   .build/marketplace/deployer/envsubst \
                   .build/marketplace/deployer/envsubst_onbuild \
                   .build/marketplace/deployer/helm \
                   .build/marketplace/deployer/helm_onbuild \
                   .build/marketplace/deployer/helm2 \
                   .build/marketplace/deployer/helm2_onbuild \
                   .build/marketplace/deployer/helm_tiller \
                   .build/marketplace/deployer/helm_tiller_onbuild


.build/marketplace: | .build
	mkdir -p "$@"


.build/marketplace/dev: \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/dev -type f) \
		$(shell find scripts -type f) \
		| .build/marketplace
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/dev/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer: | .build/marketplace
	mkdir -p "$@"


.build/marketplace/deployer/envsubst: \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_envsubst_base -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_envsubst_base/Dockerfile \
	    .
	@touch "$@"

.build/marketplace/deployer/envsubst_onbuild: \
		.build/marketplace/deployer/envsubst \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_envsubst_base/onbuild -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --build-arg FROM="gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:$(MARKETPLACE_TOOLS_TAG)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst/onbuild:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_envsubst_base/onbuild/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm: \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_helm_base -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm_onbuild: \
		.build/marketplace/deployer/helm \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_helm_base/onbuild -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --build-arg FROM="gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$(MARKETPLACE_TOOLS_TAG)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_base/onbuild/Dockerfile \
	    .
	@touch "$@"

.build/marketplace/deployer/helm2: \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_helm2_base -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm2:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm2_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm2_onbuild: \
		.build/marketplace/deployer/helm2 \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_helm2_base/onbuild -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --build-arg FROM="gcr.io/cloud-marketplace-tools/k8s/deployer_helm2:$(MARKETPLACE_TOOLS_TAG)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm2/onbuild:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm2_base/onbuild/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm_tiller: \
		.build/var/MARKETPLACE_TOOLS_TAG \
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_helm_tiller_base -type f) \
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
		$(shell find marketplace/deployer_util -type f) \
		$(shell find marketplace/deployer_helm_tiller_base/onbuild -type f) \
		| .build/marketplace/deployer
	$(call print_target)
	docker build \
	    --build-arg FROM="gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller:$(MARKETPLACE_TOOLS_TAG)" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm_tiller/onbuild:$(MARKETPLACE_TOOLS_TAG)" \
	    -f marketplace/deployer_helm_tiller_base/onbuild/Dockerfile \
	    .
	@touch "$@"


endif
