# Replace this file with functional code rather than one that just lists the S3 buckets.
import json
import logging
import os

import boto3
import urllib3

from utils.environment_helpers import validate_env_variable

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", None)

############################################
# - API FUNCTIONS
############################################


def fetch_judgment_urllib(api_endpoint, query, username, pw):
    """
    Fetch the judgment from the National Archives
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("GET", url, headers=headers)
    print("Fetch judgment status:", r.status)
    print("Fetch judgment data:", r.data)
    return r.data.decode()


def lock_judgment_urllib(api_endpoint, query, username, pw):
    """
    Lock the judgment for editing
    """
    http = urllib3.PoolManager()
    url = f"{api_endpoint}lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("PUT", url, headers=headers)
    print("Lock judgment API status:", r.status)
    # return r.data.decode()


def check_lock_judgment_urllib(api_endpoint, query, username, pw):
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


def read_message(message):
    """
    Return the status and URI of the judgment
    """
    json_body = json.dumps(message)
    json_message = json.loads(json_body)
    message = json_message["Message"]
    message_read = json.loads(message)
    print(message_read)
    status = message_read["status"]
    query = message_read["uri_reference"]

    return status, query


def upload_contents(source_key, xml_content):
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key + ".xml"
    LOGGER.info("Uploading XML content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3", endpoint_url=AWS_ENDPOINT_URL)
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=xml_content)


def process_event(sqs_rec, api_endpoint):
    """
    Function to check the status of the judgment, fetch the judgment if it is published, lock the judgment for editing
    and upload to destination S3 bucket
    """
    message = json.loads(sqs_rec["body"])
    status, query = read_message(message)
    print("Judgment status:", status)
    print("Judgment query:", query)

    if status == "published":
        print("Judgment:", query)
        source_key = query.replace("/", "-")
        print("Source key:", source_key)

        # fetch the xml content
        xml_content = fetch_judgment_urllib(
            api_endpoint, query, API_USERNAME, API_PASSWORD
        )
        # print(xml_content)
        upload_contents(source_key, xml_content)
        lock_judgment_urllib(api_endpoint, query, API_USERNAME, API_PASSWORD)
        check_lock_judgment_urllib(api_endpoint, query, API_USERNAME, API_PASSWORD)
    else:
        print("Judgment not published.")


############################################
# LAMBDA HANDLER
############################################

DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
API_USERNAME = validate_env_variable("API_USERNAME")
API_PASSWORD = validate_env_variable("API_PASSWORD")
ENVIRONMENT = validate_env_variable("ENVIRONMENT")


def handler(event, context):
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Lambda to fetch XML judgment via API")
    LOGGER.info("Destination bucket for XML judgment: %s", DEST_BUCKET)
    LOGGER.info(ENVIRONMENT)

    if ENVIRONMENT == "staging":
        api_endpoint = "https://api.staging.caselaw.nationalarchives.gov.uk/"
    else:
        api_endpoint = "https://api.caselaw.nationalarchives.gov.uk/"

    try:
        LOGGER.info("SQS EVENT: %s", event)
        for sqs_rec in event["Records"]:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec, api_endpoint)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
