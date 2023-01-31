#!/usr/bin/env python3

import json
import logging
import os
import urllib.parse

import boto3

from utils.helper import parse_file

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


def process_event(sqs_rec):
    """
    Isolating processing from event unpacking for portability and testing
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
        sqs_rec["s3"]["object"]["key"], encoding="utf-8"
    )
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = (
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )

    # extract the judgement contents
    text_content = extract_text_content(file_content)
    upload_contents(source_key, text_content)


def extract_text_content(file_content):
    """
    Extract text from the content elements of the XML file
    """
    file_content = parse_file(file_content)
    return file_content


def upload_contents(source_key, text_content):
    """
    Uploads text to S3 bucket
    """
    filename = os.path.splitext(source_key)[0] + ".txt"
    LOGGER.info("Uploading text content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=text_content)


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")


def handler(event, context):
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Extract judgement contents from XML")
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
