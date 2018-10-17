ifndef __TESTING_MAKEFILE__

__TESTING_MAKEFILE__ := included

include common.Makefile
include gcloud.Makefile
include marketplace.Makefile

TEST_ID := $(shell cat /dev/urandom | tr -dc 'a-z0-9' | head -c 8)

.testing/marketplace/deployer/helm_tiller_onbuild:
	mkdir -p $@

.testing/marketplace/deployer/helm_tiller_onbuild/helm-dependency-build: \
		.build/marketplace/deployer/helm_tiller_onbuild \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find testing/deployer_helm_tiller_base/helm-dependency-build -type f) \
    | .testing/marketplace/deployer/helm_tiller_onbuild
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./testing/marketplace/deployer/helm_tiller_onbuild/helm-dependency-build/test

.testing/marketplace/deployer/helm_tiller_onbuild/standard: \
		.build/marketplace/deployer/helm_tiller_onbuild \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find testing/deployer_helm_tiller_base/standard -type f) \
    | .testing/marketplace/deployer/helm_tiller_onbuild
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./testing/marketplace/deployer/helm_tiller_onbuild/standard/test

.PHONY: testing/marketplace/deployer/helm_tiller_onbuild
testing/marketplace/deployer/helm_tiller_onbuild: \
		.testing/marketplace/deployer/helm_tiller_onbuild/helm-dependency-build \
		.testing/marketplace/deployer/helm_tiller_onbuild/standard
	;

endif
