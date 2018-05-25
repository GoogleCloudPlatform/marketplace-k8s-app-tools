ifndef __COMMON_MAKEFILE__

__COMMON_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/var.Makefile


MARKETPLACE_TOOLS_PATH ?= $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))


.PHONY: tools_path_exists
tools_path_exists:
ifeq ($(shell test -d "$(MARKETPLACE_TOOLS_PATH)" && echo "OK"),)
	$(error '$(MARKETPLACE_TOOLS_PATH)' directory does not exist. Must set proper path for marketplace tools)
endif


.build: | tools_path_exists
	mkdir -p .build


.PHONY: clean
clean:
	rm -Rf .build


endif
