### Images publishing ###

include marketplace.Makefile
include tests.Makefile

### Testing ###

.PHONY: lint/py
lint/py: .build/tests/py
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  --entrypoint python3 \
	  tests/py \
	  -m yapf --style yapf --recursive --diff \
	  --exclude "data/vendor/" \
	  --parallel \
	  "/data" \
	  || (echo ">>> Linting failed. Run 'make format/py' to fix your code."; exit 1)
	@docker run --rm \
	  -v $(PWD):/data:ro \
	  --entrypoint python3 \
	  tests/py \
	  -m pyflakes "/data"
	@$(call print_notice,No lint errors found.)


.PHONY: format/py
format/py: .build/tests/py
	@docker run --rm \
	  -v $(PWD):/data \
	  --entrypoint python3 \
	  tests/py \
	  -m yapf --style yapf --recursive --in-place \
	  --exclude "data/vendor/" \
	  --verbose --parallel \
	  "/data"
