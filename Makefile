### Images publishing ###

include marketplace.Makefile
include testing.Makefile

### Testing ###

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
