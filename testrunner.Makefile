ifndef __TESTRUNNER_MAKEFILE__

__TESTRUNNER_MAKEFILE__ := included

include common.Makefile

.build/testrunner: | .build/tmp
	$(call print_target)
	cd testrunner \
	  && bazel build //runner:main
	rm -rf .build/tmp/testrunner
	mkdir -p .build/tmp/testrunner
	cp testrunner/bazel-bin/runner/main .build/tmp/testrunner/testrunner
	docker build --tag=testrunner --file=testrunner/runner/Dockerfile .build/tmp/testrunner
	@touch "$@"


endif
