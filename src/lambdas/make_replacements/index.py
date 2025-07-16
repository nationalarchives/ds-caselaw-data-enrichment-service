import json
import logging
import os

import boto3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from replacer.make_replacements import make_post_header_replacements
from utils.custom_types import DocumentAsXMLString
from utils.environment_helpers import validate_env_variable

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def upload_contents(source_key: str, dest_bucket: str, text_content: DocumentAsXMLString) -> None:
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key

    LOGGER.info("Uploading text content to %s/%s", dest_bucket, filename)
    s3 = boto3.resource("s3")
    s3_obj = s3.Object(dest_bucket, filename)
    s3_obj.put(Body=text_content)


def process_event(sqs_rec: SQSRecord, dest_bucket: str, source_bucket: str, replacements_bucket: str) -> None:
    """
    Isolating processing from event unpacking for portability and testing
    """
    s3_client = boto3.client("s3")

    message = json.loads(sqs_rec["body"])
    LOGGER.info("EVENT: %s", message)

    msg_attributes = sqs_rec["messageAttributes"]
    source_key = msg_attributes["source_key"]["stringValue"]

    replacement_bucket = msg_attributes["source_bucket"]["stringValue"]
    LOGGER.info("Replacement bucket from message")
    LOGGER.info(replacement_bucket)

    LOGGER.info(replacements_bucket)
    LOGGER.info("Source_key")
    LOGGER.info(source_key)

    filename = os.path.splitext(source_key)[0] + ".xml"

    LOGGER.info(source_bucket)
    LOGGER.info("Filename")
    LOGGER.info(filename)

    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=source_bucket, Key=filename)["Body"].read().decode("utf-8"),
    )
    LOGGER.info("Fetched original XML file content")

    replacement_file_content = (
        s3_client.get_object(Bucket=replacements_bucket, Key=source_key)["Body"].read().decode("utf-8")
    )
    LOGGER.info("Fetched replacement mapping file")

    if replacement_file_content:
        LOGGER.info("Applying replacements to the original XML content")
        updated_xml_file_content = make_post_header_replacements(file_content, replacement_file_content)
    else:
        LOGGER.info("Replacement mapping file is empty, so no replacements will be made.")
        updated_xml_file_content = file_content

    upload_contents(filename, dest_bucket, updated_xml_file_content)

    LOGGER.info("Uploaded updated XML file content to destination bucket")


# make replacements
@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Make replacements")
    DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
    LOGGER.info(DEST_BUCKET)
    SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET_NAME")
    LOGGER.info(SOURCE_BUCKET)
    REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")
    LOGGER.info(REPLACEMENTS_BUCKET)
    try:
        LOGGER.info("SQS EVENT: %s", event)

        for sqs_rec in event.records:
            # stop the test notification event from breaking the parsing logic
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec, DEST_BUCKET, SOURCE_BUCKET, REPLACEMENTS_BUCKET)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
