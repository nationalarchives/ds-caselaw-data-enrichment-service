#!/usr/bin/env python3

import logging
import urllib.parse

import boto3
from aws_lambda_powertools.utilities.data_classes import S3Event, event_source
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from oblique_references.enrich_oblique_references import (
    enrich_oblique_references,
)

from utils.environment_helpers import validate_env_variable
from utils.types import DocumentAsXMLString

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def upload_contents(source_key: str, output_file_content: DocumentAsXMLString) -> None:
    """
    Upload enriched file to S3 bucket
    """
    filename = source_key
    destination_bucket = validate_env_variable("DEST_BUCKET")
    LOGGER.info("Uploading enriched file to %s/%s", destination_bucket, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(destination_bucket, filename)
    object.put(Body=output_file_content)


def process_event(sqs_rec: S3EventRecord) -> None:
    """
    Function to fetch the XML, call the oblique references pipeline and upload the enriched XML to the
    destination bucket
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec.s3.bucket.name
    source_key = urllib.parse.unquote_plus(sqs_rec.s3.get_object.key, encoding="utf-8")
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"]
        .read()
        .decode("utf-8"),
    )

    enriched_content = enrich_oblique_references(file_content)

    upload_contents(source_key, enriched_content)


@event_source(data_class=S3Event)
def handler(event: S3Event, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("detect-oblique-references")
    try:
        LOGGER.info("SQS EVENT: %s", event)

        for sqs_rec in event.records:
            # stop the test notification event from breaking the parsing logic
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
