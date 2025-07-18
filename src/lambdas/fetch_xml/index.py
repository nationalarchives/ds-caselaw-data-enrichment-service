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

    if r.status != 200:
        error_msg = f"Failed to fetch judgment from {url}, status code: {r.status}, response: {r.data.decode()}"
        LOGGER.error(error_msg)
        raise RuntimeError(error_msg)

    LOGGER.info(f"Successfully fetched judgment from {url}")
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

    if r.status != 201:
        error_msg = f"Failed to lock judgment from {url}, status code: {r.status}, response: {r.data.decode()}"
        LOGGER.error(error_msg)
        raise RuntimeError(error_msg)

    LOGGER.info("Judgment locked successfully")


def check_lock_judgment_urllib(api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str) -> bool:
    """
    Check whether the judgment is locked
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)

    r = http.request("GET", url, headers=headers)

    if r.status != 200:
        error_msg = f"Failed to check lock status from {url}, status code: {r.status}, response: {r.data.decode()}"
        LOGGER.error(error_msg)
        raise RuntimeError(error_msg)

    response_data = json.loads(r.data.decode())
    locked = response_data["status"] == "Locked"

    if locked:
        LOGGER.info("Judgment is locked")
    else:
        LOGGER.info("Judgment is not locked")
    return locked


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


def upload_contents(source_key: str, xml_content: DocumentAsXMLString, dest_bucket: str) -> None:
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key + ".xml"
    LOGGER.info("Uploading XML content to %s/%s", dest_bucket, filename)
    s3 = boto3.resource("s3")
    s3_obj = s3.Object(dest_bucket, filename)
    s3_obj.put(Body=xml_content)


def process_event(
    sqs_rec: SQSRecord,
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
    dest_bucket: str,
) -> None:
    """Fetch the judgment xml, upload it to S3, and lock it for editing."""
    message = json.loads(sqs_rec.body)
    status, uri_reference = read_message(message)
    print("Judgment status:", status)
    print("Judgment uri:", uri_reference)

    xml_content = fetch_judgment_urllib(api_endpoint, uri_reference, api_username, api_password)
    lock_judgment_urllib(api_endpoint, uri_reference, api_username, api_password)
    locked = check_lock_judgment_urllib(api_endpoint, uri_reference, api_username, api_password)

    if not locked:
        error_message = "Judgment was not locked successfully."
        LOGGER.error(error_message)
        raise RuntimeError(error_message)

    upload_contents(uri_reference, xml_content, dest_bucket)


############################################
# LAMBDA HANDLER
############################################


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    # Initialize environment variables
    dest_bucket = validate_env_variable("DEST_BUCKET_NAME")
    api_username = validate_env_variable("API_USERNAME")
    api_password = validate_env_variable("API_PASSWORD")
    environment = validate_env_variable("ENVIRONMENT")

    LOGGER.info("Lambda to fetch XML judgment via API")
    LOGGER.info("Destination bucket for XML judgment: %s", dest_bucket)
    LOGGER.info(environment)

    if environment == "staging":
        api_endpoint = APIEndpointBaseURL("https://api.staging.caselaw.nationalarchives.gov.uk/")
    else:
        api_endpoint = APIEndpointBaseURL("https://api.caselaw.nationalarchives.gov.uk/")

    try:
        LOGGER.info("SQS EVENT: %s", event)
        for sqs_rec in event.records:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(
                sqs_rec,
                api_endpoint,
                api_username,
                api_password,
                dest_bucket,
            )

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
