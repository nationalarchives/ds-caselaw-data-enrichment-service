SHELL := /bin/bash

.PHONY: test

test:
	poetry run pytest ${TEST_ARGS}
