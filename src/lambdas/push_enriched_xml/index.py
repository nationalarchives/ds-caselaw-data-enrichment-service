import json
import logging

import boto3
import requests
import urllib3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from lxml import etree
from requests.auth import HTTPBasicAuth

from utils.custom_types import APIEndpointBaseURL, DocumentAsXMLString
from utils.environment_helpers import validate_env_variable

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


############################################
# - API FUNCTIONS
############################################


def fetch_judgment_urllib(api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str) -> DocumentAsXMLString:
    """
    Fetch the judgment from the National Archives
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)

    r = http.request("GET", url, headers=headers)

    if r.status != 200:
        error_msg = f"Failed to fetch judgment from {url}, status code: {r.status}, response: {r.data.decode()}"
        LOGGER.error(error_msg)
        raise RuntimeError(error_msg)

    LOGGER.info("Successfully fetched judgment at %s", query)

    return DocumentAsXMLString(r.data.decode())


def release_lock(api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str) -> None:
    """
    Unlock the judgment after editing
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)

    r = http.request("DELETE", url, headers=headers)

    if r.status != 200:
        error_msg = f"Failed to release lock from {url}, status code: {r.status}, response: {r.data.decode()}"
        LOGGER.error(error_msg)
        raise RuntimeError(error_msg)

    LOGGER.info("Successfully released lock for %s", query)


def patch_judgment_request(
    api_endpoint: APIEndpointBaseURL,
    document_uri: str,
    data: str,
    username: str,
    pw: str,
) -> None:
    """
    Apply enrichments to the judgment
    """
    response = requests.patch(
        f"{api_endpoint}judgment/{document_uri}",
        auth=HTTPBasicAuth(username, pw),
        data=data.encode(),
        params={"unlock": True},
        timeout=10,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_msg = (
            f"Failed to patch judgment {document_uri}, status code: {response.status_code}, response: {response.text}"
        )
        LOGGER.error(error_msg)
        raise RuntimeError(error_msg) from e


############################################


def process_event(sqs_rec: SQSRecord) -> None:
    """
    Function to apply enrichments to the judgment
    """
    s3_client = boto3.client("s3")

    message = json.loads(sqs_rec.body)
    LOGGER.info("EVENT: %s", message)
    msg_attributes = sqs_rec["messageAttributes"]
    source_bucket = msg_attributes["source_bucket"]["stringValue"]
    source_key = msg_attributes["source_key"]["stringValue"]
    validated_file = message["Validated"]
    LOGGER.info("Source bucket from message")
    LOGGER.info(source_bucket)
    LOGGER.info("Source key from message")
    LOGGER.info(source_key)
    LOGGER.info("Validated file from message")
    LOGGER.info(validated_file)

    if ENVIRONMENT == "staging":
        api_endpoint = APIEndpointBaseURL("https://api.staging.caselaw.nationalarchives.gov.uk/")
    else:
        api_endpoint = APIEndpointBaseURL("https://api.caselaw.nationalarchives.gov.uk/")

    # Fetch the xml as bytes as etree.fromstring does not support encoding declarations in the XML
    # when in string format.
    file_content: bytes = s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"].read()

    # Canonicalize the xml with C14N 1.0 so that only the apex node defines the namespaces
    # and the attributes are in the same order.
    # This is important for the API to accept the XML.
    # Note C14N 2.0 is not supported by the API and further the XML should not have
    # sub namespaces defined in the child nodes; they are only there due to the way the XML is
    # generated and ideally we would fix that, but for now this is a quick way to get things into shape.
    tree = etree.fromstring(file_content)
    canonical_xml = etree.tostring(tree, method="c14n").decode("utf-8")

    document_uri = source_key.replace(".xml", "")
    LOGGER.info("Document URI from message")
    LOGGER.info(document_uri)

    # patch the judgment
    patch_judgment_request(api_endpoint, document_uri, canonical_xml, API_USERNAME, API_PASSWORD)


############################################
# - INSTANTIATE CLASS HELPERS
# - GET ENV VARIABLES
############################################


SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET")
API_USERNAME = validate_env_variable("API_USERNAME")
API_PASSWORD = validate_env_variable("API_PASSWORD")
ENVIRONMENT = validate_env_variable("ENVIRONMENT")


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("push-xml")
    LOGGER.info(SOURCE_BUCKET)
    LOGGER.info(API_USERNAME)
    LOGGER.info(ENVIRONMENT)
    try:
        LOGGER.info("SQS EVENT: %s", event)
        for sqs_rec in event.records:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
