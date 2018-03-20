ifndef __COMMON_MAKEFILE__

__COMMON_MAKEFILE__ := included


MARKETPLACE_TOOLS_PATH ?= $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: common/setup
common/setup: | .build
ifeq ($(shell test -d $(MARKETPLACE_TOOLS_PATH) && echo "OK"),)
	$(error $(MARKETPLACE_TOOLS_PATH) directory does not exist. Must set proper path for marketplace tools)
endif

.build:
	mkdir -p .build

.PHONY: clean
clean:
	rm -Rf .build


endif
