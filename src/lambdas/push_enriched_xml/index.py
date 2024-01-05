import json
import logging

import boto3
import requests
import urllib3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from requests.auth import HTTPBasicAuth

from utils.environment_helpers import validate_env_variable
from utils.types import APIEndpointBaseURL, DocumentAsXMLString

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


############################################
# - API FUNCTIONS
############################################


def fetch_judgment_urllib(
    api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str,
) -> DocumentAsXMLString:
    """
    Fetch the judgment from the National Archives
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("GET", url, headers=headers)
    print(r.status)
    print(r.data)
    return DocumentAsXMLString(r.data.decode())


def release_lock(
    api_endpoint: APIEndpointBaseURL, query: str, username: str, pw: str,
) -> None:
    """
    Unlock the judgment after editing
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("DELETE", url, headers=headers)
    print(r.status)
    print(r.data)


def patch_judgment_request(
    api_endpoint: APIEndpointBaseURL, query: str, data: str, username: str, pw: str,
) -> None:
    """
    Apply enrichments to the judgment
    """
    response = requests.patch(
        f"{api_endpoint}judgment/{query}",
        auth=HTTPBasicAuth(username, pw),
        data=data.encode(),
    )
    print(response)
    response.raise_for_status()


############################################


def process_event(sqs_rec: SQSRecord) -> None:
    """
    Function to apply enrichments to the judgment
    """
    s3_client = boto3.client("s3")

    message = json.loads(sqs_rec.body)
    LOGGER.info("EVENT: %s", message)
    msg_attributes = sqs_rec["messageAttributes"]
    validated_file = message["Validated"]
    source_key = msg_attributes["source_key"]["stringValue"]

    source_bucket = msg_attributes["source_bucket"]["stringValue"]
    LOGGER.info("Source bucket from message")
    LOGGER.info(source_bucket)
    LOGGER.info("Validated file from message")
    LOGGER.info(validated_file)

    if ENVIRONMENT == "staging":
        api_endpoint = APIEndpointBaseURL(
            "https://api.staging.caselaw.nationalarchives.gov.uk/",
        )
    else:
        api_endpoint = APIEndpointBaseURL(
            "https://api.caselaw.nationalarchives.gov.uk/",
        )

    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"]
        .read()
        .decode("utf-8"),
    )

    print(source_key)
    judgment_uri = source_key.replace("-", "/").split(".")[0]
    print(judgment_uri)

    # patch the judgment
    patch_judgment_request(
        api_endpoint, judgment_uri, file_content, API_USERNAME, API_PASSWORD,
    )

    # release the lock
    release_lock(api_endpoint, judgment_uri, API_USERNAME, API_PASSWORD)


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
