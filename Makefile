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
$(PYTHON_TEST_DIRS): %: .build/testing/py
	$(info === Running tests in directory $@ ===)
	@docker run -it --rm \
	  -v $(PWD):/data \
	  testing/py \
	  python2 -m unittest discover -s "/data/$@" -p "*_test.py"


.build:
	mkdir -p .build


.PHONY: clean
clean:
	rm -Rf .build


.build/testing: | .build
	mkdir -p .build/testing


.build/testing/py: testing/py/Dockerfile | testing/setup
	docker build -t testing/py testing/py
	@touch $@


.PHONY: testing/setup
testing/setup: | .build/testing
	@ which docker > /dev/null || (echo "Please install docker"; exit 1)
