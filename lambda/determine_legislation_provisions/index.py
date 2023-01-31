#!/usr/bin/env python3

import csv
import datetime
import logging
import os
import urllib.parse

import boto3
from bs4 import BeautifulSoup

from legislation_provisions_extraction.legislation_provisions import provisions_pipeline
from replacer.second_stage_replacer import provision_replacement

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

    LOGGER.info("Uploading enriched file to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=output_file_content)


def add_timestamp_and_engine_version(file_data):
    """
    Add today's timestamp and version at time of enrichment
    """
    soup = BeautifulSoup(file_data, "xml")
    today = datetime.datetime.now()
    today_str = today.strftime("%Y-%m-%dT%H:%M:%S")
    enriched_date = soup.new_tag(
        'FRBRdate date="{}" name="tna-enriched"'.format(today_str)
    )
    enrichment_version = soup.new_tag("uk:tna-enrichment-engine")
    enrichment_version.string = "0.1.0"
    soup.FRBRManifestation.FRBRdate.insert_after(enriched_date)
    soup.proprietary.append(enrichment_version)
    return soup


def process_event(sqs_rec):
    """
    Function to fetch the XML, call the legislation provisions extraction pipeline and upload the enriched XML to the
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

    resolved_refs = provisions_pipeline(file_content)
    print(resolved_refs)

    if resolved_refs:
        soup = BeautifulSoup(file_content, "xml")
        output_file_data = provision_replacement(soup, resolved_refs)
        timestamp_added = add_timestamp_and_engine_version(output_file_data)
        upload_contents(source_key, str(timestamp_added))
    else:
        timestamp_added = add_timestamp_and_engine_version(file_content)
        upload_contents(source_key, str(timestamp_added))


DEST_BUCKET = validate_env_variable("DEST_BUCKET")


def handler(event, context):
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("detect-legislation-provisions")
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
