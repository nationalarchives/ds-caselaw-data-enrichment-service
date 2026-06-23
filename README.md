# The National Archives: Find Case Law

This repository is part of the [Find Case Law](https://caselaw.nationalarchives.gov.uk/) project at [The National Archives](https://www.nationalarchives.gov.uk/). For more information on the project, check [the documentation](https://github.com/nationalarchives/ds-find-caselaw-docs).

# Judgment Enrichment Pipeline

![Tests](https://img.shields.io/github/actions/workflow/status/nationalarchives/ds-caselaw-data-enrichment-service/ci.yml?branch=main&label=tests)
![Code Coverage](https://img.shields.io/codecov/c/github/nationalarchives/ds-caselaw-data-enrichment-service)

Marks up judgments in [Find Case Law](https://caselaw.nationalarchives.gov.uk) with references to other cases and legislation.

# Description of system

[A description of the system's architecture](DESCRIPTION.md)

## Development Setup

### Local Environment

Install all dependencies (including test dependencies) for local development:

```bash
make setup
```

This uses Poetry to install:

- Core dependencies: `boto3`, `botocore`, `aws-lambda-powertools`, `pandas`, `psycopg2-binary`, `sqlalchemy`
- Lambda-specific groups: `enrichment-lambda`, `legislation-lambda`, `rules-lambda`, `backup-lambda`
- Test dependencies: `pytest`, `pytest-cov`, `moto`, `testcontainers`, etc.

All dependencies are managed centrally in `pyproject.toml` with a locked `poetry.lock` file for reproducible builds.

### Dependency Management

- **Single source of truth**: `pyproject.toml` at repository root
- **Locked versions**: `poetry.lock` ensures reproducible builds across environments
- **Lambda groups**: Each lambda function has an optional dependency group:
  - `enrichment-lambda`: spacy, beautifulsoup4, lxml, requests (NLP and XML processing)
  - `legislation-lambda`: sparqlwrapper (SPARQL queries)
  - `rules-lambda`: spacy (NLP processing)
  - `backup-lambda`: none (uses core deps only)
  - `test`: pytest, moto, testcontainers, coverage, etc.

### Updating Dependencies

To update a dependency version (e.g., update boto3):

```bash
poetry update boto3
make test  # Verify changes don't break tests
```

To add a new dependency to a lambda group:

```bash
poetry add --group enrichment-lambda new-package-name
```

To sync your environment after poetry.lock changes:

```bash
poetry install
```

## Tests

There is a suite of tests that can be run locally with:

```bash
make test
```

This automatically cleans assembly artifacts and runs:

```bash
poetry run pytest ${TEST_ARGS}
```

You can also run pytest directly:

```bash
PYTHONPATH=src poetry run pytest
```

To run specific tests:

```bash
make test TEST_ARGS="src/tests/caselaw_extraction_tests/"
make test TEST_ARGS="-k test_xml_parser"
```

### Database-backed tests

Some tests require a PostgreSQL database. This is handled automatically using Testcontainers:

- Each test (or test fixture) starts a temporary PostgreSQL container
- The container is created and destroyed automatically during the test run
- No local PostgreSQL installation is required

#### Prerequisites

- **Docker**: Must be installed and running (required by Testcontainers)
- **Python 3.13+**: With Poetry installed
- **On Mac**: libpq must be installed and on PATH (for psycopg2):
  ```bash
  brew install libpq
  PATH="/opt/homebrew/opt/libpq/bin:$PATH" && make test
  ```

#### Test configuration

Test configuration is managed via pytest fixtures in `conftest.py`. These fixtures automatically set up:

- A temporary PostgreSQL instance using testcontainers
- SQLAlchemy database engine and session
- NLP pipeline (spaCy with entity ruler)
- Preloaded database tables for integration tests

No manual database setup or external services required.

#### Test execution

- Tests run in isolation
- A fresh PostgreSQL instance is created per test session
- All fixtures clean up automatically after completion

#### Test markers

Run only integration tests (tests requiring PostgreSQL):

```bash
make test TEST_ARGS="-m integration"
```

Run tests excluding integration tests:

```bash
make test TEST_ARGS="-m 'not integration'"
```

### Coverage report

You can obtain a coverage report with:

```bash
coverage run --source . -m pytest
coverage report
```

### CI execution

Tests are executed in CI as part of the GitHub Actions workflow (.github/workflows/ci.yml).

## Building and Validating Lambda Functions

Use Make targets as the single public interface for local and CI validation/builds.

## Make Targets Reference

### Development & Testing

| Target                      | Description                                                                  |
| --------------------------- | ---------------------------------------------------------------------------- |
| `make setup`                | Install all dependencies for development and testing                         |
| `make test`                 | Run all tests with pytest                                                    |
| `make test TEST_ARGS="..."` | Run tests with custom pytest args (e.g., `-k test_name` or `-m integration`) |

### Building & Validation

| Target                            | Description                                                                |
| --------------------------------- | -------------------------------------------------------------------------- |
| `make build-lambdas`              | Build all Lambda Docker images for local testing                           |
| `make build-lambda LAMBDA=<name>` | Build one Lambda image                                                     |
| `make smoke-test`                 | Test all Lambda containers using AWS Lambda Runtime Interface (RIE)        |
| `make smoke-test LAMBDA=<name>`   | Test one specific Lambda container (used by CI matrix for parallelization) |
| `make validate`                   | Full validation pipeline: test → build-lambdas → smoke-test                |
| `make clean`                      | Clean Docker build artifacts                                               |

### Smoke Testing Strategy

**Local:** `make smoke-test` builds Lambda Docker images and validates them with AWS Lambda Runtime Interface Emulator (RIE). Runs all 4 lambdas sequentially, or with `LAMBDA=<name>` for a single lambda.

**CI/CD:** `.github/workflows/ci.yml` runs unit tests first, then invokes `make smoke-test LAMBDA=<name>` for each lambda in parallel (4 jobs). `.github/workflows/deploy_single_environment.yml` builds and smoke tests all 4 lambdas in parallel before pushing to ECR, ensuring broken images never reach production.

**Full validation:** `make validate` runs unit tests → builds all lambdas → smoke tests all containers. This is the comprehensive pre-commit gate.

Build principles:

- One dependency source of truth: `pyproject.toml` + `poetry.lock`
- Selective COPY in Dockerfiles (not full `src/`): Preserves build cache granularity
- Dependencies installed before source: Code changes don't force dependency reinstall
- One build implementation: `make build-lambda`
- Consistent behavior across local, PR CI, and deploy CI

Where implementation details live:

- Build orchestration: `Makefile`
- Lambda image definitions: `src/lambdas/*/Dockerfile`
- CI pipeline: `.github/workflows/ci.yml` (unit tests → parallel smoke tests)
- Deployment pipeline: `.github/workflows/deploy_single_environment.yml` (parallel build → smoke test → ECR push → Terraform deploy)

## Repository Structure and Build Process

The `src/` directory contains all code used by both tests and Docker builds:

```
src/
├── lambdas/                    # Lambda entry points (enrichment, legislation, rules, backup)
├── enrichment/                 # Enrichment modules
├── database/                   # Shared database utilities
└── utils/                      # Shared utilities
```

**Testing with absolute imports:** `pytest.ini` adds `src/` to pythonpath, enabling:

```python
from lambdas.enrichment_lambda.api import read_message
from utils.environment_helpers import validate_env_variable
```

**Docker builds:** Dockerfiles at `src/lambdas/{lambda_name}/Dockerfile` are built with `docker build -f "src/lambdas/$(LAMBDA)/Dockerfile" -t $(LAMBDA):local .`

- Install dependencies first (Poetry layers reused across code changes)
- Selectively copy only: `src/utils/`, `src/database/`, `src/lambdas/{name}/`, and `src/enrichment/` (enrichment_lambda only)
- Result: Build caches stay granular; code changes don't force dependency reinstall

## Turning Enrichment Off

There are a number of places where enrichment can be turned off:

- Marklogic Username/Password
  - Go to the production Marklogic interface, "Admin" (top), "Security" (left), "Users" (left), "enrichment-engine" (mid).
  - Make sure you know where the password is stored so you can put access back afterwards!
  - Changing the password will mean no Enrichment processes can interact with Marklogic -- no getting documents, no uploading them
  - Messages will still be sent from the Editor interface, and will build up.
  - Purge the queues in AWS before turning Enrichment back on. The database will not load stale documents due to locks expiring.
  - Seemed to work well last time, but there were a lot of warnings

- AWS Lambda that fetches XML
  - Not actually tested in anger!
  - Log into `da-caselaw-enrichment`. Make sure to switch to `eu-west-2`/`London`.
  - In Lambda, Functions, select `tna-s3-tna-production-fetch-xml`
  - Top left, press Throttle.
  - This will prevent any ingestion of the incoming messages which will build up
  - Anything currently in process will finish and will continue to run to completion
  - You can change the concurrency settings to unthrottle it
  - Note that manual changes to the lambda settings will likely be lost if new code is deployed

- Modifying the code
  - We could change either the code in one of the lambdas -- probably `fetch_xml` or
    `push_enriched_xml` for the start/end of the process
  - We could also modify the privileged API, but that potentially affect all users of it
    but there aren't any at the time of writing

## Debugging

Situations when you may want to debug an enrichment run:

- a document we expect to have been enriched, has not been enriched as expected.
- an AWS error alert for a lambda function has been raised to us (probably through email notification subscription)

The main ways we have to debug are to look at `AWS` [logs](https://eu-west-2.console.aws.amazon.com/cloudwatch/home?region=eu-west-2#logsV2:log-groups) for `lambda` functions and data stored in [s3 buckets](https://s3.console.aws.amazon.com/s3/buckets?region=eu-west-2) but we need appropriate information to find these in AWS first.

You will need access to for the staging or production Enrichment AWS space as appropriate to follow these debugging tips. If not, you could skip most of this and attempt at recreating a local test of a lambda function you think might have a problem like in [Recreate and debug](#recreate-and-debug)

### Getting information to investigate in AWS

[`tools/see_prod.html`](https://html-preview.github.io/?url=https://github.com/nationalarchives/ds-caselaw-data-enrichment-service/blob/master/tools/see_prod.html) will allow you to search the AWS logs for a specific judgment by URL and link directly to files generated on production.

### Validating XML

If you run `scripts/get_schema`, the schema will be downloaded, and `scripts/validate_local <xmlfile>` will check it complies with the schema

## Deployment

<!-- last_review: 2026-04-13 -->

Currently, the `main` branch is deployed to staging, and if that doesn't fail, it is then automatically deployed to production.

## Release versioning

The version should be an integer string (like "1"): note, however, that pre-December 2023 versions were version "0.1.0".

As a part of each pull request that isn't just keeping versions up to date:

- Update the version number in `enrichment_version.string` in `src/lambdas/determine_legislation_provisions/index.py`
- Update `CHANGELOG.md` with a brief description of the change
- Create a release on Github with a tag like `v1`. This does nothing, but is useful to help us keep track.
