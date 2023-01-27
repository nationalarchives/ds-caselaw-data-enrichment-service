import csv
import json
import logging
import os
import urllib

import boto3
import requests
import urllib3
from botocore.exceptions import ClientError
from requests.auth import HTTPBasicAuth

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def validate_env_variable(env_var_name):
    LOGGER.debug(f"Getting the value of the environment variable: {env_var_name}")

    try:
        env_variable = os.environ[env_var_name]
    except KeyError:
        raise Exception(f"Please, set environment variable {env_var_name}")

    if not env_variable:
        raise Exception(f"Please, provide environment variable {env_var_name}")

    return env_variable


############################################
# - API FUNCTIONS
############################################


def fetch_judgment_urllib(query, username, pw):
    """
    Fetch the judgment from the National Archives
    """
    http = urllib3.PoolManager()
    url = f"https://api.staging.caselaw.nationalarchives.gov.uk/judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("GET", url, headers=headers)
    print(r.status)
    print(r.data)
    return r.data.decode()


def patch_judgment(query, data, username, pw):
    """
    Apply enrichments to the judgment
    """
    http = urllib3.PoolManager()
    url = f"https://api.staging.caselaw.nationalarchives.gov.uk/judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("PATCH", url, headers=headers, fields=data)
    print(r.status)
    print(r.data)
    return r.data.decode()


def release_lock(query, username, pw):
    """
    Unlock the judgment after editing
    """
    http = urllib3.PoolManager()
    url = f"https://api.staging.caselaw.nationalarchives.gov.uk/lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("DELETE", url, headers=headers)
    print(r.status)
    print(r.data)
    return r.data.decode()


def patch_judgment_request(query, data, username, pw):
    """
    Apply enrichments to the judgment
    """
    response = requests.patch(
        f"https://api.staging.caselaw.nationalarchives.gov.uk/judgment/{query}",
        auth=HTTPBasicAuth(username, pw),
        data=data.encode(),
    )
    print(response)
    print(response.content)


############################################


def process_event(sqs_rec):
    """
    Function to apply enrichments to the judgment 
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
        sqs_rec["s3"]["object"]["key"], encoding="utf-8"
    )
    print("Input S3 bucket:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = (
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )
    LOGGER.info(file_content)

    print(source_key)
    judgment_uri = source_key.replace("-", "/").split(".")[0]
    print(judgment_uri)

    # patch the judgment
    patch_judgment_request(judgment_uri, file_content, API_USERNAME, API_PASSWORD)

    # release the lock
    release_lock(judgment_uri, API_USERNAME, API_PASSWORD)


############################################
# - INSTANTIATE CLASS HELPERS
# - GET ENV VARIABLES
############################################


SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET")
API_USERNAME = validate_env_variable("API_USERNAME")
API_PASSWORD = validate_env_variable("API_PASSWORD")
ENVIRONMENT = validate_env_variable("ENVIRONMENT")


def handler(event, context):
    """
    Function called by the lambda to run the process event     
    """
    LOGGER.info("push-xml")
    LOGGER.info(SOURCE_BUCKET)
    LOGGER.info(API_USERNAME)
    LOGGER.info(ENVIRONMENT)
    try:
        LOGGER.info("SQS EVENT: %s", event)
        for sqs_rec in event["Records"]:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
