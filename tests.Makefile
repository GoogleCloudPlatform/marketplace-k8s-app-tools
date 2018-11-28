ifndef __TESTS_MAKEFILE__

__TESTS_MAKEFILE__ := included

include common.Makefile
include gcloud.Makefile
include marketplace.Makefile

TEST_ID := $(shell cat /dev/urandom | tr -dc 'a-z0-9' | head -c 8)

.tests/marketplace/deployer/helm_tiller_onbuild:
	mkdir -p "$@"

.tests/marketplace/deployer/helm_tiller_onbuild/helm-dependency-build: \
		.build/marketplace/deployer/helm_tiller_onbuild \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find tests/marketplace/deployer_helm_tiller_base/onbuild/helm-dependency-build -type f) \
		tests.Makefile \
		| .tests/marketplace/deployer/helm_tiller_onbuild
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./tests/marketplace/deployer_helm_tiller_base/onbuild/helm-dependency-build/run_test
	@touch "$@"


.tests/marketplace/deployer/helm_tiller_onbuild/standard: \
		.build/marketplace/deployer/helm_tiller_onbuild \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find tests/marketplace/deployer_helm_tiller_base/onbuild/standard -type f) \
		tests.Makefile \
		| .tests/marketplace/deployer/helm_tiller_onbuild
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./tests/marketplace/deployer_helm_tiller_base/onbuild/standard/run_test
	@touch "$@"


.PHONY: tests/marketplace/deployer/helm_tiller_onbuild
tests/marketplace/deployer/helm_tiller_onbuild: \
		.tests/marketplace/deployer/helm_tiller_onbuild/helm-dependency-build \
		.tests/marketplace/deployer/helm_tiller_onbuild/standard


.tests/marketplace/deployer/envsubst:
	mkdir -p "$@"

.tests/marketplace/deployer/envsubst/standard: \
		.build/marketplace/deployer/envsubst \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find tests/marketplace/deployer_envsubst_base/standard -type f) \
		tests.Makefile \
		| .tests/marketplace/deployer/envsubst
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./tests/marketplace/deployer_envsubst_base/standard/run_test
	@touch "$@"

.tests/marketplace/deployer/envsubst/full: \
		.build/marketplace/deployer/envsubst \
		.build/marketplace/dev \
		.build/var/MARKETPLACE_TOOLS_TAG \
		.build/var/REGISTRY \
		$(shell find tests/marketplace/deployer_envsubst_base/full -type f) \
		tests.Makefile \
		| .tests/marketplace/deployer/envsubst
	$(call print_target)
	TEST_ID=$(TEST_ID) \
	REGISTRY=$(REGISTRY) \
	MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
	  ./tests/marketplace/deployer_envsubst_base/full/run_test
	@touch "$@"

.PHONY: tests/marketplace/deployer/envsubst
tests/marketplace/deployer/envsubst: \
		.tests/marketplace/deployer/envsubst/full \
		.tests/marketplace/deployer/envsubst/standard


.PHONY: tests/integration
tests/integration: \
		tests/marketplace/deployer/envsubst \
		tests/marketplace/deployer/helm_tiller_onbuild



PYTHON_TEST_DIRS = $(shell find . \
                     -path ./vendor -prune -o \
                     -name "*_test.py" -type f -print \
                     | xargs -n 1 dirname | sort | uniq)

# Append .__pytest__ to all python test directories to generate targets.
PYTHON_TEST_TARGETS = $(foreach f,$(PYTHON_TEST_DIRS),$(f).__pytest__)


.PHONY: tests/py
tests/py: $(PYTHON_TEST_TARGETS)
	@$(call print_notice,All tests passed.)


.PHONY: $(PYTHON_TEST_TARGETS)
$(PYTHON_TEST_TARGETS): %.__pytest__: .build/tests/py
	$(info === Running tests in directory $* ===)
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  --entrypoint python2 \
	  tests/py \
	  -m unittest discover -s "/data/$*" -p "*_test.py"

.build/tests: | .build
	mkdir -p "$@"


.build/tests/py: tests/py/Dockerfile | .build/tests
	$(call print_target)
	docker build -t tests/py tests/py
	@touch "$@"


endif
