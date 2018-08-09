ifndef __TESTRUNNER_MAKEFILE__

__TESTRUNNER_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile


.build/testrunner: | .build/tmp
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH)/testrunner \
	  && bazel build //runner:main
	rm -rf .build/tmp/testrunner
	mkdir -p .build/tmp/testrunner
	cp $(MARKETPLACE_TOOLS_PATH)/testrunner/bazel-bin/runner/main .build/tmp/testrunner/testrunner
	docker build --tag=testrunner --file=$(MARKETPLACE_TOOLS_PATH)/testrunner/runner/Dockerfile .build/tmp/testrunner
	@touch "$@"

endif
