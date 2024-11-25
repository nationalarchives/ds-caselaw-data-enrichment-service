# The National Archives: Find Case Law

This repository is part of the [Find Case Law](https://caselaw.nationalarchives.gov.uk/) project at [The National Archives](https://www.nationalarchives.gov.uk/). For more information on the project, check [the documentation](https://github.com/nationalarchives/ds-find-caselaw-docs).

# Judgment Enrichment Pipeline

![Tests](https://img.shields.io/github/actions/workflow/status/nationalarchives/ds-caselaw-data-enrichment-service/ci_lint_and_test.yml?branch=main&label=tests) ![Coverage](https://img.shields.io/codeclimate/coverage/nationalarchives/ds-caselaw-data-enrichment-service) ![Maintainability](https://img.shields.io/codeclimate/maintainability/nationalarchives/ds-caselaw-data-enrichment-service)

Marks up judgments in [Find Case Law](https://caselaw.nationalarchives.gov.uk) with references to other cases and legislation.

# Description of system

[A description of the system's architecture](DESCRIPTION.md)

## Tests

There is a suite of tests that can be run locally with `pytest -m "not integration"` or `scripts/test`
but you'll need to ensure you've installed the requirements in `src/tests/requirements.txt`

You can also obtain a test coverage report with `coverage run --source . -m pytest && coverage report`

The tests are currently run in CI as specified in `.github/workflows/ci_lint_and_test.yml`

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

## Deploy

Currently, the `main` branch is deployed to staging, and if that doesn't fail, it is then deployed to production.

#### Release Process

The version should be an integer string (like "1"): note, however, that pre-December 2023 versions were version "0.1.0".

As a part of each pull request that isn't just keeping versions up to date:

- Update the version number in `enrichment_version.string` in `src/lambdas/determine_legislation_provisions/index.py`
- Update `CHANGELOG.md` with a brief description of the change
- Create a release on Github with a tag like `v1`. This does nothing, but is useful to help us keep track.
