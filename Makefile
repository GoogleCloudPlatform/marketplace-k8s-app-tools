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

### Testing ###

PYTHON_TEST_DIRS = $(shell find . \
                     -path ./vendor -prune -o \
                     -name "*_test.py" -type f -print \
                     | xargs -n 1 dirname | sort | uniq)

# Append .__pytest__ to all python test directories to generate targets.
PYTHON_TEST_TARGETS = $(foreach f,$(PYTHON_TEST_DIRS),$(f).__pytest__)


.PHONY: lint/py
lint/py: .build/testing/py
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  --entrypoint python2 \
	  testing/py \
	  -m yapf --style chromium --recursive --diff \
	  --exclude "data/vendor/" \
	  --parallel \
	  "/data" \
	  || (echo ">>> Linting failed. Run 'make format/py' to fix your code."; exit 1)
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  --entrypoint python2 \
	  testing/py \
	  -m pyflakes "/data"
	@$(call print_notice,No lint errors found.)


.PHONY: format/py
format/py: .build/testing/py
	@docker run --rm \
	  -v $(PWD):/data \
	  --entrypoint python2 \
	  testing/py \
	  -m yapf --style chromium --recursive --in-place \
	  --exclude "data/vendor/" \
	  --verbose --parallel \
	  "/data"


.PHONY: test/py
test/py: $(PYTHON_TEST_TARGETS)
	@$(call print_notice,All tests passed.)


.PHONY: $(PYTHON_TEST_TARGETS)
$(PYTHON_TEST_TARGETS): %.__pytest__: .build/testing/py
	$(info === Running tests in directory $* ===)
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  --entrypoint python2 \
	  testing/py \
	  -m unittest discover -s "/data/$*" -p "*_test.py"


.build/testing: | .build
	mkdir -p "$@"


.build/testing/py: testing/py/Dockerfile | .build/testing
	$(call print_target)
	docker build -t testing/py -f testing/py/Dockerfile .
	@touch "$@"
