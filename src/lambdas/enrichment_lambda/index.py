import json
import logging

import boto3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext

from lambdas.enrichment_lambda.api import fetch_judgment, lock_judgment, patch_judgment, read_message
from lambdas.enrichment_lambda.steps import (
    add_timestamp_and_engine_version,
    determine_abbreviation_replacements,
    determine_caselaw_replacements,
    determine_legislation_replacements,
    enrich_oblique_references,
    make_post_header_replacements,
    make_replacements_input,
    replace_legislation_provisions,
)
from utils.custom_types import APIEndpointBaseURL, DocumentAsXMLString
from utils.environment_helpers import validate_env_variable
from utils.helper import parse_file

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def enrich_xml_file(xml: str, pattern_list: list[dict], enrichment_version: str = "7.4.0") -> str:
    # all run on original XML sequentially, so that replacements are applied before enrichment
    parsed_xml = parse_file(DocumentAsXMLString(xml))
    caselaw_replacements = determine_caselaw_replacements(parsed_xml, pattern_list)

    legislation_replacements = determine_legislation_replacements(parsed_xml)
    abbreviation_replacements = determine_abbreviation_replacements(parsed_xml)

    # create a single JSON string of all replacements to pass to the replacer
    replacement_file_content = make_replacements_input(
        caselaw_replacements,
        abbreviation_replacements,
        legislation_replacements,
    )

    # appply the basic replacements to the XML, before enriching with oblique references and legislation provisions
    xml_with_replacements = make_post_header_replacements(DocumentAsXMLString(xml), replacement_file_content)

    # then enrich with oblique references and legislation provisions
    xml_with_oblique_references = enrich_oblique_references(xml_with_replacements)
    fully_enriched_xml = replace_legislation_provisions(xml_with_oblique_references)

    # add timestamp and engine version to the fully enriched XML
    fully_enriched_xml_with_timestamp = add_timestamp_and_engine_version(
        fully_enriched_xml,
        enrichment_version,
    )
    return fully_enriched_xml_with_timestamp


def process_event(
    uri_reference: str,
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
    pattern_list: list[dict],
) -> None:
    LOGGER.info("Enriching judgment: %s", uri_reference)

    LOGGER.info("Fetching judgment from API endpoint: %s", api_endpoint)
    xml_content = fetch_judgment(api_endpoint, uri_reference, api_username, api_password)

    LOGGER.info("Locking judgment: %s", uri_reference)
    lock_judgment(api_endpoint, uri_reference, api_username, api_password)

    LOGGER.info("Enriching judgment content for: %s", uri_reference)
    enriched_xml = enrich_xml_file(xml_content, pattern_list, enrichment_version="7.4.0")

    LOGGER.info("Patching enriched judgment back to API endpoint: %s", api_endpoint)
    patch_judgment(api_endpoint, uri_reference, enriched_xml, api_username, api_password)

    LOGGER.info("Successfully enriched and patched: %s", uri_reference)


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    num_records = len(list(event.records))
    LOGGER.info("Received SQS event with %d records", num_records)
    api_username = validate_env_variable("API_USERNAME")
    api_password = validate_env_variable("API_PASSWORD")
    environment = validate_env_variable("ENVIRONMENT")
    rules_bucket = validate_env_variable("RULES_FILE_BUCKET")
    rules_key = validate_env_variable("RULES_FILE_KEY")

    LOGGER.info("Enrichment Lambda triggered, environment: %s", environment)

    LOGGER.info("Fetching rules from S3 bucket: %s, key: %s", rules_bucket, rules_key)
    s3 = boto3.client("s3")
    patterns_resp = s3.get_object(Bucket=rules_bucket, Key=rules_key)
    patterns = patterns_resp["Body"].read().decode("utf-8")
    pattern_list = [json.loads(line) for line in patterns.splitlines()]

    if environment == "staging":
        api_endpoint = APIEndpointBaseURL("https://api.staging.caselaw.nationalarchives.gov.uk/")
    else:
        api_endpoint = APIEndpointBaseURL("https://api.caselaw.nationalarchives.gov.uk/")

    for sqs_rec in event.records:
        if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
            continue
        try:
            LOGGER.info("Processing SQS record: %s", sqs_rec.message_id)
            message = json.loads(sqs_rec.body)
            _status, uri_reference = read_message(message)
            process_event(uri_reference, api_endpoint, api_username, api_password, pattern_list)
            LOGGER.info("Successfully processed SQS record: %s", sqs_rec.message_id)
        except Exception as exc:
            LOGGER.error("Failed to process record: %s", exc)
            raise
    LOGGER.info("Successfully enriched and patched all %d records in the SQS event", num_records)
