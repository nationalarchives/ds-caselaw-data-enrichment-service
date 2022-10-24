import boto3
from botocore.exceptions import ClientError
import requests
from requests.auth import HTTPBasicAuth
import os
import json
import logging
import urllib.parse

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


def check_lock_status(query, username, pw):
    response = requests.get(
                f"https://api.staging.caselaw.nationalarchives.gov.uk/lock/{query}",
                auth=HTTPBasicAuth(username, pw))
    lock_status = json.loads(response.content)
    return lock_status


def fetch_judgment(query, username, pw):
    response = requests.get(
                f"https://api.staging.caselaw.nationalarchives.gov.uk/judgment/{query}",
                auth=HTTPBasicAuth(username, pw))
    judgment = response.content.decode('utf-8')
    # judgment = json.loads(response.content)
    return judgment


def fetch_and_lock_judgment(query, username, pw):
    response = requests.put(
                f"https://api.staging.caselaw.nationalarchives.gov.uk/lock/{query}",
                auth=HTTPBasicAuth(username, pw))
    judgment = response.content.decode('utf-8')
    return judgment


def release_lock(query, username, pw):
    response = requests.delete(
                f"https://api.staging.caselaw.nationalarchives.gov.uk/lock/{query}",
                auth=HTTPBasicAuth(username, pw))
    print(response.content)


def upload_contents(source_key, xml_content):
    filename = source_key + ".xml"
    LOGGER.info('Uploading XML content to %s/%s', DEST_BUCKET, filename)
    s3 = boto3.resource('s3')
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=xml_content)


def process_event(sqs_rec):
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
                sqs_rec["s3"]["object"]["key"], encoding="utf-8"
            )
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    # message = json.loads(sqs_rec['body'])
    message = sqs_rec['body']
    query = message['uri_reference']
    print("Query:", query)
    query_split = query.split('/')
    source_key = query_split[2]+'-'+query_split[0]+'-'+query_split[3]+'-'+query_split[1]

    # fetch the xml content
    xml_content = fetch_judgment(query, API_USERNAME, API_PASSWORD)
    upload_contents(source_key, xml_content)


SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET")
API_USERNAME = validate_env_variable("API_USERNAME")
API_PASSWORD = validate_env_variable("API_PASSWORD")

def handler(event, context):
    try:
        client = boto3.client("s3")
        response = client.list_buckets()
        buckets = []
        for bucket in response['Buckets']:
            buckets += {bucket["Name"]}

    except ClientError:
        print("Error")
        raise
    else:
        return
