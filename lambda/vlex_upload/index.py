#!/usr/bin/env python3

import logging
import json
import urllib.parse
import os
import boto3

from distutils.util import strtobool

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

def validate_env_variable(env_var_name):
    print(f"Getting the value of the environment variable: {env_var_name}")

    try:
        env_variable = os.environ[env_var_name]
    except KeyError:
        raise Exception(f"Please, set environment variable {env_var_name}")

    if not env_variable:
        raise Exception(f"Please, provide environment variable {env_var_name}")

    return env_variable


# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec):

    if not FORWARD_TO_VLEX_ENABLED:
        return False

    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
                sqs_rec["s3"]["object"]["key"], encoding="utf-8"
            )
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = s3_client.get_object(
                Bucket=source_bucket, Key=source_key)["Body"].read()

    upload_contents(file_content)
    LOGGER.debug("content uploaded")
    return True

def upload_contents(source_key, text_content):
    # store the file contents in the destination bucket
    # LOGGER.info(os.path.splitext(source_key)[0])
    filename = os.path.splitext(source_key)[0] + ".txt"
            # filename = source_key.print(os.path.splitext("/path/to/some/file.txt")[0])
    LOGGER.info('uploading text content to %s/%s', DEST_BUCKET, filename)
    s3 = boto3.resource('s3')
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=text_content)

DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
FORWARD_TO_VLEX_ENABLED = strtobool(validate_env_variable("FORWARD_TO_VLEX_ENABLED"))

def handler(event, context):
    LOGGER.info("vlex_upload")
    LOGGER.info(DEST_BUCKET)
    try:
        LOGGER.info('SQS EVENT: %s', event)

        for sqs_rec in event['Records']:
            # TODO make the code adapt to a direct invocation vs reading from an SQS queue

            # stop the test notification event from breaking the parsing logic
            if 'Event' in sqs_rec.keys() and sqs_rec['Event'] == 's3:TestEvent':
                break
            uploaded = process_event(sqs_rec)
            LOGGER.info("uploaded=" + uploaded)

    except Exception as exception:
        LOGGER.error('Exception: %s', exception)
        raise