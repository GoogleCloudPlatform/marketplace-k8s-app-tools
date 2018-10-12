ifndef __COMMON_MAKEFILE__

__COMMON_MAKEFILE__ := included

define print_target
  @$(call print_notice,Building $@...)
endef

define print_notice
  printf "\n\033[93m\033[1m$(1)\033[0m\n"
endef

define print_error
  printf "\n\033[93m\033[1m$(1)\033[0m\n"
endef

makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/var.Makefile


# MARKETPLACE_TOOLS_PATH is the path to the root of the
# marketplace-k8s-app-tools submodule. We derive it here by taking the
# full path of the directory containing this common.Makefile. patsubst
# operation removes the trailing slash.
MARKETPLACE_TOOLS_PATH ?= $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

$(info ---- MARKETPLACE_TOOLS_PATH = $(MARKETPLACE_TOOLS_PATH))

# MARKETPLACE_TOOLS_TAG is the tag of the container images published
# by marketplace-k8s-app-tools.
MARKETPLACE_TOOLS_TAG := $(shell cd $(MARKETPLACE_TOOLS_PATH) && scripts/derive_tag.sh)
export MARKETPLACE_TOOLS_TAG

$(info ---- MARKETPLACE_TOOLS_TAG = $(MARKETPLACE_TOOLS_TAG))


.build: | tools_path_exists
	mkdir -p "$@"


.build/tmp: | .build
	mkdir -p "$@"


.PHONY: clean
clean::
	rm -Rf .build


.PHONY: tools_path_exists
tools_path_exists:
ifeq ($(shell test -d "$(MARKETPLACE_TOOLS_PATH)" && echo "OK"),)
	$(error '$(MARKETPLACE_TOOLS_PATH)' directory does not exist. Must set proper path for marketplace tools)
endif


endif
