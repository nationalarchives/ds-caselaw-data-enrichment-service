#!/usr/bin/env python3

import json
import logging
import os

import boto3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from replacer.make_replacments import make_post_header_replacements
from utils.environment_helpers import validate_env_variable
from utils.types import DocumentAsXMLString

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def upload_contents(source_key: str, text_content: DocumentAsXMLString) -> None:
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key

    LOGGER.info("Uploading text content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=text_content)


def process_event(sqs_rec: SQSRecord) -> None:
    """
    Isolating processing from event unpacking for portability and testing
    """
    s3_client = boto3.client("s3")

    message = json.loads(sqs_rec["body"])
    LOGGER.info("EVENT: %s", message)

    msg_attributes = sqs_rec["messageAttributes"]
    message["replacements"]
    source_key = msg_attributes["source_key"]["stringValue"]

    replacement_bucket = msg_attributes["source_bucket"]["stringValue"]
    LOGGER.info("Replacement bucket from message")
    LOGGER.info(replacement_bucket)

    LOGGER.info(REPLACEMENTS_BUCKET)
    LOGGER.info("Source_key")
    LOGGER.info(source_key)

    filename = os.path.splitext(source_key)[0] + ".xml"

    LOGGER.info(SOURCE_BUCKET)
    LOGGER.info("Filename")
    LOGGER.info(filename)

    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=SOURCE_BUCKET, Key=filename)["Body"]
        .read()
        .decode("utf-8"),
    )
    LOGGER.info("Got original XML file content")

    replacement_file_content = (
        s3_client.get_object(Bucket=REPLACEMENTS_BUCKET, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )
    LOGGER.info("Got replacement file content")

    full_replaced_text_content = make_post_header_replacements(
        file_content, replacement_file_content,
    )
    upload_contents(filename, full_replaced_text_content)


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET_NAME")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")


# make replacements
@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Make replacements")
    LOGGER.info(DEST_BUCKET)
    LOGGER.info(SOURCE_BUCKET)
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
