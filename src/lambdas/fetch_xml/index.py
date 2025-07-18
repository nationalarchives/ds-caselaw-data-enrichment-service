import json
import logging
from typing import Any

import boto3
import urllib3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

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
    print("Fetch judgment status:", r.status)
    print("Fetch judgment data:", r.data)
    return DocumentAsXMLString(r.data.decode())


def lock_judgment_urllib(api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str) -> None:
    """
    Lock the judgment for editing
    """
    http = urllib3.PoolManager()
    # currently unlock only looks for a truthy/falsy value
    # but we might upgrade that to be a time in seconds
    url = f"{api_endpoint}lock/{query}?unlock=3600"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request(
        "PUT",
        url,
        headers=headers,
    )
    print("Lock judgment API status:", r.status)
    # return r.data.decode()


def check_lock_judgment_urllib(api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str) -> None:
    """
    Check whether the judgment is locked
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("GET", url, headers=headers)
    print("Check lock status:", r.status)
    print("Check lock data:", r.data.decode())
    # return r.data.decode()


############################################
# OTHER FUNCTIONS
############################################


def read_message(message_dict: dict[Any, Any]) -> tuple[str, str]:
    """
    Return the status and URI of the judgment
    """
    json_body = json.dumps(message_dict)
    json_message = json.loads(json_body)
    message = json_message["Message"]
    message_read = json.loads(message)
    print(message_read)
    status = message_read["status"]
    uri_reference = message_read["uri_reference"]

    return status, uri_reference


def upload_contents(source_key: str, xml_content: DocumentAsXMLString) -> None:
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key + ".xml"
    LOGGER.info("Uploading XML content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    s3_obj = s3.Object(DEST_BUCKET, filename)
    s3_obj.put(Body=xml_content)


def process_event(sqs_rec: SQSRecord, api_endpoint: APIEndpointBaseURL) -> None:
    """Fetch the judgment xml, upload it to S3, and lock it for editing."""
    message = json.loads(sqs_rec.body)
    status, uri_reference = read_message(message)
    print("Judgment status:", status)
    print("Judgment uri:", uri_reference)

    xml_content = fetch_judgment_urllib(api_endpoint, uri_reference, API_USERNAME, API_PASSWORD)

    upload_contents(uri_reference, xml_content)
    lock_judgment_urllib(api_endpoint, uri_reference, API_USERNAME, API_PASSWORD)
    check_lock_judgment_urllib(api_endpoint, uri_reference, API_USERNAME, API_PASSWORD)


############################################
# LAMBDA HANDLER
############################################

DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
API_USERNAME = validate_env_variable("API_USERNAME")
API_PASSWORD = validate_env_variable("API_PASSWORD")
ENVIRONMENT = validate_env_variable("ENVIRONMENT")


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Lambda to fetch XML judgment via API")
    LOGGER.info("Destination bucket for XML judgment: %s", DEST_BUCKET)
    LOGGER.info(ENVIRONMENT)

    if ENVIRONMENT == "staging":
        api_endpoint = APIEndpointBaseURL("https://api.staging.caselaw.nationalarchives.gov.uk/")

    else:
        api_endpoint = APIEndpointBaseURL("https://api.caselaw.nationalarchives.gov.uk/")

    try:
        LOGGER.info("SQS EVENT: %s", event)
        for sqs_rec in event.records:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec, api_endpoint)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
