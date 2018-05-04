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


PYTHON_TEST_DIRS = $(shell find . -name "*_test.py" | xargs -n 1 dirname | sort | uniq)


.PHONY: test/py
test/py: $(PYTHON_TEST_DIRS)


.PHONY: $(PYTHON_TEST_DIRS)
$(PYTHON_TEST_DIRS): %:
	$(info === Running tests in directory $@ ===)
	@python -m unittest discover -s "$@" -p "*_test.py"
