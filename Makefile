.PHONY: submodule/init
submodule/init:
	git submodule init
	git submodule sync --recursive
	git submodule update --init --recursive


.PHONY: submodule/init-force
submodule/init-force:
	git submodule init
	git submodule sync --recursive
	git submodule update --init --recursive --force


# Find directories that contain python tests.
PYTHON_TEST_DIRS = $(shell find . -name "*_test.py" | xargs -n 1 dirname | sort | uniq)


.PHONY: clean
clean:
	rm -Rf .build


.PHONY: test/py
test/py: $(PYTHON_TEST_DIRS)


.PHONY: $(PYTHON_TEST_DIRS)
$(PYTHON_TEST_DIRS): %: .build/testing/py
	$(info === Running tests in directory $@ ===)
	@docker run --rm \
	  -v $(PWD):/data \
	  testing/py \
	  python2 -m unittest discover -s "/data/$@" -p "*_test.py"


.build:
	mkdir -p "$@"


.build/testing: | .build
	mkdir -p "$@"


.build/testing/py: testing/py/Dockerfile | .build/testing
	docker build -t testing/py testing/py
	@touch "$@"
