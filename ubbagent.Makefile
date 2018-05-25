ifndef __UBBAGENT_MAKEFILE__

__UBBAGENT_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/base_containers.Makefile
include $(makefile_dir)/var.Makefile

UBBAGENT_BUILD = .build/marketplace-ubbagent

$(UBBAGENT_BUILD):
	mkdir -p $(UBBAGENT_BUILD)

$(UBBAGENT_BUILD)/ubbagent: .build/var/MARKETPLACE_REGISTRY| ubbagent/setup
	cd $(MARKETPLACE_TOOLS_PATH)/vendor/ubbagent \
	&& docker build \
	      --tag "$(MARKETPLACE_REGISTRY)/ubbagent" \
	      .
	gcloud docker -- push "$(MARKETPLACE_REGISTRY)/ubbagent"
	@touch "$@"

# Target for invoking directly with make. Don't use this as a prerequisite
# if your target needs to build the ubbagent container.
# Use $(UBBAGENT_BUILD)/ubbagent instead.
.PHONY: ubbagent/build
ubbagent/build: $(UBBAGENT_BUILD) ;

.PHONY: ubbagent/setup
ubbagent/setup: | base/setup $(UBBAGENT_BUILD)


endif
