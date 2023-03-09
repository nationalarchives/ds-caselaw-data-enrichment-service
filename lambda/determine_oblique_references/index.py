#!/usr/bin/env python3

import logging
import os
import urllib.parse

import boto3

from oblique_references.enrich_oblique_references import (
    enrich_oblique_references,
)

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


def upload_contents(source_key, output_file_content):
    """
    Upload enriched file to S3 bucket
    """
    filename = source_key
    destination_bucket = validate_env_variable("DEST_BUCKET")
    LOGGER.info("Uploading enriched file to %s/%s", destination_bucket, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(destination_bucket, filename)
    object.put(Body=output_file_content)


def process_event(sqs_rec):
    """
    Function to fetch the XML, call the oblique references pipeline and upload the enriched XML to the
    destination bucket
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

    enriched_content = enrich_oblique_references(file_content)

    upload_contents(source_key, enriched_content)




def handler(event, context):
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("detect-oblique-references")
    try:
        LOGGER.info("SQS EVENT: %s", event)

        for sqs_rec in event["Records"]:
            # stop the test notification event from breaking the parsing logic
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise