#!/usr/bin/env python3

import logging
import urllib.parse
import os
import boto3
from bs4 import BeautifulSoup
import re
from oblique_references.oblique_references import oblique_pipeline
from replacer.second_stage_replacer import oblique_replacement

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
    filename = source_key

    LOGGER.info("Uploading enriched file to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=output_file_content)


def process_event(sqs_rec):

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
    # LOGGER.info(file_content)

    # split file_content into header and judgment to ensure replacements only occur in judgment body
    judgment_split = re.split("(</header>)", file_content)

    resolved_refs = oblique_pipeline(judgment_split[2])

    if resolved_refs:
        output_file_data = oblique_replacement(judgment_split[2], resolved_refs)
        # combine header with replaced text content before uploading to enriched bucket
        judgment_split[2] = output_file_data
        full_replaced_text_content = "".join(judgment_split)
        upload_contents(source_key, full_replaced_text_content)
    else:
        upload_contents(source_key, file_content)


DEST_BUCKET = validate_env_variable("DEST_BUCKET")


def handler(event, context):
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
