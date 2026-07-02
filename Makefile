SHELL := /bin/bash

.PHONY: setup test test-e2e build-lambdas build-lambda smoke-test validate clean

setup:
	@echo "Setting up local development environment..."
	poetry install --with enrichment-lambda,legislation-lambda,rules-lambda,backup-lambda,test
	@echo "Development environment ready. Use 'make test' to run tests or 'make build-lambdas' to build."

test:
	poetry run pytest -m "not e2e" ${TEST_ARGS}

test-e2e:
	poetry run pytest -m e2e src/tests/end_to_end_tests/test_marklogic_e2e.py -rs -vvv -s -q ${TEST_ARGS}

build-lambdas:
	@for lambda in src/lambdas/*/; do \
		if [ -f "$$lambda/Dockerfile" ]; then \
			name=$$(basename $$lambda); \
			$(MAKE) build-lambda LAMBDA=$$name || exit 1; \
		fi \
	done

build-lambda:
	@if [ -z "$(LAMBDA)" ]; then \
		echo "Usage: make build-lambda LAMBDA=<lambda_name>"; \
		echo "Available lambdas: $$(ls src/lambdas/)"; \
		exit 1; \
	fi
	@echo "Building $(LAMBDA)..."
	docker build -f "src/lambdas/$(LAMBDA)/Dockerfile" -t $(LAMBDA):local .

smoke-test:
	@if [ -z "$(LAMBDA)" ]; then \
		echo "Running smoke tests for all lambdas..."; \
		$(MAKE) build-lambdas; \
		lambdas="enrichment_lambda update_legislation_table update_rules_processor db_backup"; \
	else \
		echo "Running smoke test for $(LAMBDA)..."; \
		docker build -f "src/lambdas/$(LAMBDA)/Dockerfile" -t $(LAMBDA):local . > /dev/null; \
		lambdas="$(LAMBDA)"; \
	fi; \
	failed=0; \
	for lambda in $$lambdas; do \
		echo ""; \
		echo "=== Smoke test: $$lambda ==="; \
		docker run -d --name $$lambda-smoke-test -p 9000:8080 $$lambda:local 2>/dev/null; \
		sleep 3; \
		if curl -s -f http://localhost:9000/2015-03-31/functions/function/invocations \
			-X POST \
			-H "Content-Type: application/json" \
			-d '{"test":"ping"}' > /dev/null 2>&1; then \
			echo "✓ $$lambda container is healthy"; \
			if [ -f "tests/lambda_tests/smoke_test_events/$${lambda}_test_event.json" ]; then \
				curl -s -X POST \
					http://localhost:9000/2015-03-31/functions/function/invocations \
					-H "Content-Type: application/json" \
					--data-binary @tests/lambda_tests/smoke_test_events/$${lambda}_test_event.json > /tmp/$${lambda}_response.json; \
				if jq empty /tmp/$${lambda}_response.json 2>/dev/null; then \
					echo "✓ $$lambda responds with valid JSON"; \
				else \
					echo "✗ $$lambda response is not valid JSON"; \
					failed=1; \
				fi; \
			fi; \
		else \
			echo "✗ $$lambda container failed to start"; \
			docker logs $$lambda-smoke-test; \
			failed=1; \
		fi; \
		docker stop $$lambda-smoke-test 2>/dev/null; \
		docker rm $$lambda-smoke-test 2>/dev/null; \
	done; \
	echo ""; \
	if [ $$failed -eq 1 ]; then \
		echo "✗ Smoke tests failed"; \
		exit 1; \
	else \
		echo "✓ Smoke tests passed"; \
	fi

validate: test build-lambdas smoke-test
	@echo ""
	@echo "✓ All validations passed!"
	@echo "  - Unit tests: PASS"
	@echo "  - Lambda builds: PASS"
	@echo "  - Smoke tests: PASS"

clean:
	@echo "Clean complete."
