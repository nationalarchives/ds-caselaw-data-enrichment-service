# Replace this file with functional code rather than one that just lists the S3 buckets.
import json
import logging
import os

import boto3
import requests
import urllib3
from botocore.exceptions import ClientError
from requests.auth import HTTPBasicAuth

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def validate_env_variable(env_var_name):
    print(f"Getting the value of the environment variable: {env_var_name}")

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
    http = urllib3.PoolManager()
    url = f"https://api.staging.caselaw.nationalarchives.gov.uk/judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("GET", url, headers=headers)
    print(r.status)
    print(r.data)
    return r.data.decode()


def lock_judgment_urllib(query, username, pw):
    http = urllib3.PoolManager()
    url = f"https://api.staging.caselaw.nationalarchives.gov.uk/lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("PUT", url, headers=headers)
    print(r.status)
    print(r.data)
    return r.data.decode()


def check_lock_judgment_urllib(query, username, pw):
    http = urllib3.PoolManager()
    url = f"https://api.staging.caselaw.nationalarchives.gov.uk/lock/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + pw)
    r = http.request("GET", url, headers=headers)
    print(r.status)
    print(r.data)
    return r.data.decode()


############################################


def upload_contents(source_key, xml_content):
    filename = source_key + ".xml"
    LOGGER.info("Uploading XML content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=xml_content)


def process_event(sqs_rec):
    # message = json.loads(sqs_rec['body'])
    message = sqs_rec["body"]
    LOGGER.info("EVENT: %s", message)
    status = message["status"]
    print('Judgment status: ', status)
    if status=='published':
        query = message["uri_reference"]
        print("Judgment:", query)
        source_key = query.replace("/", "-")
        print('Source key:', source_key)

        # fetch the xml content
        xml_content = fetch_judgment_urllib(query, API_USERNAME, API_PASSWORD)
        # print(xml_content)
        upload_contents(source_key, xml_content)
        lock_judgment_urllib(query, API_USERNAME, API_PASSWORD)
        check_lock_judgment_urllib(query, API_USERNAME, API_PASSWORD)
    else:
        print('Judgment not published.')


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
API_USERNAME = validate_env_variable("API_USERNAME")
API_PASSWORD = validate_env_variable("API_PASSWORD")


def handler(event, context):
    LOGGER.info("fetch-xml")
    LOGGER.info(DEST_BUCKET)
    try:
        LOGGER.info("SQS EVENT: %s", event)
        for sqs_rec in event["Records"]:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
