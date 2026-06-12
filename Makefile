SHELL := /bin/bash

.PHONY: test test-unit

test:
	bash scripts/test_with_postgres.sh $(TEST_ARGS)

test-unit:
	PYTHONPATH=src poetry run pytest -m "not integration"
