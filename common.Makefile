ifndef __COMMON_MAKEFILE__

__COMMON_MAKEFILE__ := included


MARKETPLACE_TOOLS_PATH ?= $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))


# TODO(https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/issues/106):
# Do not require the local file system to have jq installed and remove this target.
.PHONY: common/setup
common/setup: | .build assert-var-MARKETPLACE_TOOLS_PATH
ifeq ($(shell test -d "$(MARKETPLACE_TOOLS_PATH)" && echo "OK"),)
	$(error '$(MARKETPLACE_TOOLS_PATH)' directory does not exist. Must set proper path for marketplace tools)
endif
# TODO(https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/issues/106):
# Do not require the local file system to have jq installed and remove this target.
	@ [ -n "$$(which jq)" ] || (echo 'Please install jq.'; exit 1)


.build:
	mkdir -p .build


.PHONY: clean
clean:
	rm -Rf .build


endif
