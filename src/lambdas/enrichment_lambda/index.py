import json
import logging
import urllib.parse
from typing import Any

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from lxml import etree

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


def _is_vcite_callback_event(event: dict[str, Any], vcite_enriched_bucket: str) -> bool:
    records = event.get("Records", [])
    return bool(records) and "s3" in records[0] and records[0]["s3"]["bucket"]["name"] == vcite_enriched_bucket


def _is_test_event(record: dict[str, Any]) -> bool:
    return "Event" in record and record["Event"] == "s3:TestEvent"


def _get_api_endpoint(environment: str) -> APIEndpointBaseURL:
    if environment == "staging":
        return APIEndpointBaseURL("https://api.staging.caselaw.nationalarchives.gov.uk/")
    return APIEndpointBaseURL("https://api.caselaw.nationalarchives.gov.uk/")


def _read_vcite_toggle() -> str:
    ssm = boto3.client("ssm")
    parameter = ssm.get_parameter(Name="vCite", WithDecryption=True)
    parameter_value = parameter["Parameter"]["Value"].strip().lower()
    LOGGER.info("vCite configuration: %s", parameter_value)
    return parameter_value


def _upload_to_vcite_bucket(vcite_bucket: str, source_key: str, xml_content: str) -> None:
    LOGGER.info("Uploading XML content to vCite input bucket: %s/%s", vcite_bucket, source_key)
    s3 = boto3.resource("s3")
    s3.Object(vcite_bucket, source_key).put(Body=xml_content.encode("utf-8"))


def _patch_from_vcite_callback(
    record: dict[str, Any],
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
) -> None:
    s3_client = boto3.client("s3")
    source_bucket = record["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"], encoding="utf-8")

    LOGGER.info("Processing vCite callback object: %s/%s", source_bucket, source_key)
    file_content = s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"].read()

    tree = etree.fromstring(file_content)
    canonical_xml = etree.tostring(tree, method="c14n").decode("utf-8")
    document_uri = source_key.replace(".xml", "")

    patch_judgment(api_endpoint, document_uri, canonical_xml, api_username, api_password)
    LOGGER.info("Patched vCite callback XML to API for: %s", document_uri)


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


def _process_sqs_enrichment_event(
    event: dict[str, Any],
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
    pattern_list: list[dict],
    vcite_enabled: bool,
    vcite_bucket: str,
) -> None:
    num_records = len(event.get("Records", []))

    for sqs_rec in event.get("Records", []):
        if _is_test_event(sqs_rec):
            continue

        LOGGER.info("Processing SQS record: %s", sqs_rec.get("messageId", "unknown"))
        message = json.loads(sqs_rec["body"])
        _status, uri_reference = read_message(message)

        LOGGER.info("Fetching judgment from API endpoint: %s", api_endpoint)
        xml_content = fetch_judgment(api_endpoint, uri_reference, api_username, api_password)

        LOGGER.info("Locking judgment: %s", uri_reference)
        lock_judgment(api_endpoint, uri_reference, api_username, api_password)

        LOGGER.info("Enriching judgment content for: %s", uri_reference)
        enriched_xml = enrich_xml_file(xml_content, pattern_list, enrichment_version="7.4.0")

        source_key = f"{uri_reference}.xml"

        if vcite_enabled:
            _upload_to_vcite_bucket(vcite_bucket, source_key, enriched_xml)
            LOGGER.info("vCite is on; uploaded to vCite input and skipped direct API patch for: %s", uri_reference)
            continue

        LOGGER.info("vCite is off; patching enriched judgment back to API endpoint: %s", api_endpoint)
        patch_judgment(api_endpoint, uri_reference, enriched_xml, api_username, api_password)
        LOGGER.info("Successfully enriched and patched: %s", uri_reference)

    LOGGER.info("Successfully processed all %d SQS records", num_records)


def _process_s3_vcite_callback_event(
    event: dict[str, Any],
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
) -> None:
    records = event.get("Records", [])
    LOGGER.info("Received S3 callback event with %d records", len(records))

    for s3_rec in records:
        if _is_test_event(s3_rec):
            continue
        _patch_from_vcite_callback(s3_rec, api_endpoint, api_username, api_password)


def handler(event: dict[str, Any], context: LambdaContext) -> None:
    records = event.get("Records", [])
    LOGGER.info("Received event with %d records", len(records))
    api_username = validate_env_variable("API_USERNAME")
    api_password = validate_env_variable("API_PASSWORD")
    environment = validate_env_variable("ENVIRONMENT")
    rules_bucket = validate_env_variable("RULES_FILE_BUCKET")
    rules_key = validate_env_variable("RULES_FILE_KEY")
    vcite_bucket = validate_env_variable("VCITE_BUCKET")
    vcite_enriched_bucket = validate_env_variable("VCITE_ENRICHED_BUCKET")

    LOGGER.info("Enrichment Lambda triggered, environment: %s", environment)
    api_endpoint = _get_api_endpoint(environment)
    vcite_enabled = _read_vcite_toggle() == "on"

    try:
        if _is_vcite_callback_event(event, vcite_enriched_bucket):
            LOGGER.info("Detected vCite callback event; processing S3 records for patching")
            _process_s3_vcite_callback_event(event, api_endpoint, api_username, api_password)
            return

        LOGGER.info("Detected SQS enrichment event; processing SQS records for enrichment")

        LOGGER.info("Fetching rules from S3 bucket: %s, key: %s", rules_bucket, rules_key)
        s3 = boto3.client("s3")
        patterns_resp = s3.get_object(Bucket=rules_bucket, Key=rules_key)
        patterns = patterns_resp["Body"].read().decode("utf-8")
        pattern_list = [json.loads(line) for line in patterns.splitlines()]

        _process_sqs_enrichment_event(
            event,
            api_endpoint,
            api_username,
            api_password,
            pattern_list,
            vcite_enabled,
            vcite_bucket,
        )
    except Exception as exc:
        LOGGER.error("Failed to process event: %s", exc)
        raise
