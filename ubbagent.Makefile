ifndef __UBBAGENT_MAKEFILE__

__UBBAGENT_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile


.build/ubbagent: | .build
	mkdir -p "$@"


.build/ubbagent/ubbagent: $(shell find "$(MARKETPLACE_TOOLS_PATH)/vendor/ubbagent" -type f ) \
                          | .build/ubbagent
	cd $(MARKETPLACE_TOOLS_PATH)/vendor/ubbagent \
	&& docker build \
	      --tag "gcr.io/cloud-marketplace-tools/ubbagent" \
	      .
	@touch "$@"


endif
