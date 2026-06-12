import json
import logging

from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from enrichment.oblique_references.enrich_oblique_references import enrich_oblique_references
from enrichment.replacer.make_replacements import make_post_header_replacements
from lambdas.enrichment_lambda.api import fetch_judgment, lock_judgment, patch_judgment, read_message
from lambdas.enrichment_lambda.steps import (
    determine_abbreviation_replacements,
    determine_caselaw_replacements,
    determine_legislation_replacements,
    replace_legislation_provisions,
)
from utils.custom_types import APIEndpointBaseURL, DocumentAsXMLString
from utils.environment_helpers import validate_env_variable
from utils.helper import parse_file

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def enrich_xml_file(xml: str) -> str:
    xml_with_oblique_references = enrich_oblique_references(DocumentAsXMLString(xml))
    xml_with_legislation_provisions = replace_legislation_provisions(xml_with_oblique_references)

    rules_bucket = validate_env_variable("RULES_FILE_BUCKET")
    rules_key = validate_env_variable("RULES_FILE_KEY")

    caselaw_replacements = determine_caselaw_replacements(xml_with_legislation_provisions, rules_bucket, rules_key)
    abbreviation_replacements = determine_abbreviation_replacements(xml_with_legislation_provisions)
    legislation_replacements = determine_legislation_replacements(xml_with_legislation_provisions)

    replacement_file_content = make_replacements_input(
        caselaw_replacements,
        abbreviation_replacements,
        legislation_replacements,
    )
    return make_post_header_replacements(DocumentAsXMLString(xml_with_legislation_provisions), replacement_file_content)


def make_replacements_input(caselaw_replacements, abbreviation_replacements, legislation_replacements) -> str:
    """
    Serialise replacement tuples into the line-delimited JSON format expected by the replacer.
    """
    tuple_file = ""
    for i in caselaw_replacements:
        tuple_file += json.dumps({f"{type(i).__name__}": list(i)}) + "\n"
    for i in abbreviation_replacements:
        tuple_file += json.dumps({f"{type(i).__name__}": list(i)}) + "\n"
    for i in legislation_replacements:
        tuple_file += json.dumps({f"{type(i).__name__}": list(i)}) + "\n"
    return tuple_file


def process_event(
    sqs_rec: SQSRecord,
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
) -> None:
    message = json.loads(sqs_rec.body)
    _status, uri_reference = read_message(message)
    LOGGER.info("Enriching judgment: %s", uri_reference)

    xml_content = fetch_judgment(api_endpoint, uri_reference, api_username, api_password)
    lock_judgment(api_endpoint, uri_reference, api_username, api_password)

    text_content = parse_file(xml_content)
    enriched_xml = enrich_xml_file(text_content)

    patch_judgment(api_endpoint, uri_reference, enriched_xml, api_username, api_password)
    LOGGER.info("Successfully enriched and patched: %s", uri_reference)


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    api_username = validate_env_variable("API_USERNAME")
    api_password = validate_env_variable("API_PASSWORD")
    environment = validate_env_variable("ENVIRONMENT")

    if environment == "staging":
        api_endpoint = APIEndpointBaseURL("https://api.staging.caselaw.nationalarchives.gov.uk/")
    else:
        api_endpoint = APIEndpointBaseURL("https://api.caselaw.nationalarchives.gov.uk/")

    LOGGER.info("Enrichment Lambda triggered, environment: %s", environment)
    for sqs_rec in event.records:
        if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
            continue
        try:
            process_event(sqs_rec, api_endpoint, api_username, api_password)
        except Exception as exc:
            LOGGER.error("Failed to process record: %s", exc)
            raise
