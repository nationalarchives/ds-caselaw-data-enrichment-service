SHELL := /bin/bash

.PHONY: setup test assemble-lambda-contexts build-lambdas build-lambda clean

setup:
	@echo "Setting up local development environment..."
	poetry install --with enrichment-lambda,legislation-lambda,rules-lambda,backup-lambda,test
	@echo "Development environment ready. Use 'make test' to run tests or 'make build-lambdas' to build."

test: clean
	poetry run pytest ${TEST_ARGS}

assemble-lambda-contexts:
	./scripts/assemble_lambda_contexts.sh

build-lambdas: assemble-lambda-contexts
	@for lambda in src/lambdas/*/; do \
		if [ -f "$$lambda/Dockerfile" ]; then \
			name=$$(basename $$lambda); \
			$(MAKE) build-lambda LAMBDA=$$name ASSEMBLED=1 || exit 1; \
		fi \
	done

build-lambda:
	@if [ -z "$(LAMBDA)" ]; then \
		echo "Usage: make build-lambda LAMBDA=<lambda_name>"; \
		echo "Available lambdas: $$(ls src/lambdas/)"; \
		exit 1; \
	fi
	@if [ "$(ASSEMBLED)" != "1" ]; then \
		$(MAKE) assemble-lambda-contexts; \
	fi
	@echo "Building $(LAMBDA)..."
	docker build -f "src/lambdas/$(LAMBDA)/Dockerfile" -t $(LAMBDA):local .

clean:
	@echo "Cleaning generated assembly files..."
	rm -rf src/lambdas/*/utils src/lambdas/*/database
	@echo "Clean complete."
