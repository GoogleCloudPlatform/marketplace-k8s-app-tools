ifndef __TESTING_MAKEFILE__

__TESTING_MAKEFILE__ := included

include common.Makefile
include gcloud.Makefile
include marketplace.Makefile

TEST_ID := $(shell cat /dev/urandom | tr -dc 'a-z0-9' | head -c 8)

.testing:
	mkdir -p "$@"

.testing/deployer_helm_tiller_base: | .testing
	mkdir -p "$@"

.testing/deployer_helm_tiller_base/1: \
		.build/marketplace/charts/marketplace-integration \
		.build/marketplace/deployer/helm_tiller \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find testing/deployer_helm_tiller_base/1 -type f) \
		.testing/deployer_helm_tiller_base
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./testing/deployer_helm_tiller_base/1/test

.testing/deployer_helm_tiller_base/2: \
		.build/marketplace/charts/marketplace-integration \
		.build/marketplace/deployer/helm_tiller \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find testing/deployer_helm_tiller_base/2 -type f) \
		.testing/deployer_helm_tiller_base
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./testing/deployer_helm_tiller_base/2/test
endif
