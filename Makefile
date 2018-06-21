include common.Makefile


### Submodule ###


.PHONY: submodule/init
submodule/init:
	git submodule init
	git submodule sync --recursive
	git submodule update --init --recursive


.PHONY: submodule/init-force
submodule/init-force:
	git submodule init
	git submodule sync --recursive
	git submodule update --init --recursive --force


### Images publishing ###


include marketplace.Makefile


# Get the tag associated with the current commit of the repo.
# If there is no tag, use the abbreviated commit hash.
TAG ?= $(shell \
    tag="$(shell git tag --points-at HEAD | head -n 1)"; \
    commit="$(shell git rev-parse HEAD | fold -w 12 | head -n 1)"; \
    echo "$${tag:-$$commit}")


.PHONY: images/deployer
images/deployer: .build/marketplace/deployer/envsubst \
                 .build/marketplace/deployer/helm
	$(call print_target)
	@$(call print_notice,Pushing with tag "$(TAG)" in addition to "latest")

	@ \
	for name in deployer_envsubst deployer_helm; do \
	  docker tag \
	      "gcr.io/cloud-marketplace-tools/k8s/$${name}:latest" \
	      "gcr.io/cloud-marketplace-tools/k8s/$${name}:$(TAG)" \
	  && docker push "gcr.io/cloud-marketplace-tools/k8s/$${name}:latest" \
	  && docker push "gcr.io/cloud-marketplace-tools/k8s/$${name}:$(TAG)"; \
	done


### Testing ###


# Find directories that contain python tests.
PYTHON_TEST_DIRS = $(shell find . -name "*_test.py" | xargs -n 1 dirname | sort | uniq)


.PHONY: test/py
test/py: $(PYTHON_TEST_DIRS)


.PHONY: $(PYTHON_TEST_DIRS)
$(PYTHON_TEST_DIRS): %: .build/testing/py
	$(info === Running tests in directory $@ ===)
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  testing/py \
	  python2 -m unittest discover -s "/data/$@" -p "*_test.py"


.build/testing: | .build
	mkdir -p "$@"


.build/testing/py: testing/py/Dockerfile | .build/testing
	$(call print_target)
	docker build -t testing/py testing/py
	@touch "$@"
