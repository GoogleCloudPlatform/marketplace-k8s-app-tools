ifndef __TESTRUNNER_MAKEFILE__

__TESTRUNNER_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile


.build/testrunner: | .build
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH)/testrunner \
	  && bazel build //runner:main \
	  && rm -rf tmp \
	  && mkdir -p tmp \
	  && cp bazel-bin/runner/main tmp/testrunner \
	  && docker build --tag=testrunner --file=runner/Dockerfile tmp
	@touch "$@"

endif
