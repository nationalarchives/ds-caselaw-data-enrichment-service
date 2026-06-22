"""Enrichment Lambda handler for processing SQS events and vCite callback events."""

import json
import logging
from typing import Any

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext

from lambdas.enrichment_lambda.api import read_message
from lambdas.enrichment_lambda.enrich_judgment import enrich_judgment
from lambdas.enrichment_lambda.patch_from_vcite_callback import patch_from_vcite_callback
from utils.custom_types import APIEndpointBaseURL
from utils.environment_helpers import validate_env_variable

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def _is_vcite_callback_event(event: dict[str, Any], vcite_enriched_bucket: str) -> bool:
    records = event.get("Records", [])
    return bool(records) and "s3" in records[0] and records[0]["s3"]["bucket"]["name"] == vcite_enriched_bucket


def _is_test_event(record: dict[str, Any]) -> bool:
    return "Event" in record and record["Event"] == "s3:TestEvent"


def _get_api_endpoint(environment: str) -> APIEndpointBaseURL:
    subdomain = "api.staging" if environment == "staging" else "api"
    return APIEndpointBaseURL(f"https://{subdomain}.caselaw.nationalarchives.gov.uk/")


def _process_vcite_callback_event(
    event: dict[str, Any],
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
) -> None:
    """Process S3 vCite callback event and patch enriched XML to API."""
    LOGGER.info("Detected vCite callback event; processing S3 records for patching")
    records = event.get("Records", [])
    num_records = len(records)
    LOGGER.info("Received S3 callback event with %d records", num_records)

    for s3_rec in records:
        if _is_test_event(s3_rec):
            continue

        patch_from_vcite_callback(s3_rec, api_endpoint, api_username, api_password)

    LOGGER.info("Successfully processed all %d S3 callback records", num_records)


def _process_sqs_enrichment_event(
    event: dict[str, Any],
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
    rules_bucket: str,
    rules_key: str,
    vcite_enabled: bool,
    vcite_bucket: str,
) -> None:
    """Process SQS enrichment event and enrich judgments."""
    LOGGER.info("Detected SQS enrichment event; processing SQS records for enrichment")

    LOGGER.info("Fetching rules from S3 bucket: %s, key: %s", rules_bucket, rules_key)
    s3 = boto3.client("s3")
    patterns_resp = s3.get_object(Bucket=rules_bucket, Key=rules_key)
    patterns = patterns_resp["Body"].read().decode("utf-8")
    pattern_list = [json.loads(line) for line in patterns.splitlines()]

    num_records = len(event.get("Records", []))
    for sqs_rec in event.get("Records", []):
        if _is_test_event(sqs_rec):
            continue

        LOGGER.info("Processing SQS record: %s", sqs_rec.get("messageId", "unknown"))
        message = json.loads(sqs_rec["body"])
        _status, uri_reference = read_message(message)

        enrich_judgment(
            uri_reference,
            api_endpoint,
            api_username,
            api_password,
            pattern_list,
            vcite_enabled,
            vcite_bucket,
        )

    LOGGER.info("Successfully processed all %d SQS records", num_records)


def handler(event: dict[str, Any], context: LambdaContext) -> None:
    records = event.get("Records", [])
    LOGGER.info("Received event with %d records", len(records))

    # Environment variables common to both events
    api_username: str = validate_env_variable("API_USERNAME")
    api_password: str = validate_env_variable("API_PASSWORD")
    environment: str = validate_env_variable("ENVIRONMENT")
    vcite_enabled: bool = validate_env_variable("VCITE_ENABLED") == "true"

    # Environment variables only for sqs enrichment event
    rules_bucket: str = validate_env_variable("RULES_FILE_BUCKET")
    rules_key: str = validate_env_variable("RULES_FILE_KEY")
    vcite_bucket: str = validate_env_variable("VCITE_BUCKET")

    # Environment variable only needed for vCite callback event
    vcite_enriched_bucket: str = validate_env_variable("VCITE_ENRICHED_BUCKET")

    LOGGER.info("Enrichment Lambda triggered, environment: %s", environment)

    api_endpoint = _get_api_endpoint(environment)

    try:
        # May delete this block if we don't want to support vCite callback events in the enrichment lambda
        if _is_vcite_callback_event(event, vcite_enriched_bucket):
            _process_vcite_callback_event(event, api_endpoint, api_username, api_password)
            return

        _process_sqs_enrichment_event(
            event,
            api_endpoint,
            api_username,
            api_password,
            rules_bucket,
            rules_key,
            vcite_enabled,
            vcite_bucket,
        )
    except Exception as exc:
        LOGGER.error("Failed to process event: %s", exc)
        raise
