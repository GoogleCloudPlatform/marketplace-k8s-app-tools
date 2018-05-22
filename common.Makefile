ifndef __COMMON_MAKEFILE__

__COMMON_MAKEFILE__ := included


MARKETPLACE_TOOLS_PATH ?= $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: common/setup
common/setup: | .build
ifeq ($(shell test -d $(MARKETPLACE_TOOLS_PATH) && echo "OK"),)
  $(error $(MARKETPLACE_TOOLS_PATH) directory does not exist. Must set proper path for marketplace tools)
endif
	# TODO(https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/issues/106):
	# Do not require the local file system to have jq installed and remove this target.
	@ [ -n "$$(which jq)" ] || (echo 'Please install jq.'; exit 1)

.build:
	mkdir -p .build

.PHONY: clean
clean:
	rm -Rf .build

assert-%:
	@ if [ "${${*}}" = "" ]; then \
	  echo "Make variable '$*' is required."; \
	  exit 1; \
	fi
	@ echo "$* = ${${*}}."

endif
