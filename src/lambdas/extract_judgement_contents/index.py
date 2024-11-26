import logging
import os
import urllib.parse

import boto3
from aws_lambda_powertools.utilities.data_classes import S3Event, event_source
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from utils.environment_helpers import validate_env_variable
from utils.helper import parse_file
from utils.types import DocumentAsXMLString

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def process_event(sqs_rec: S3EventRecord):
    """
    Isolating processing from event unpacking for portability and testing
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec.s3.bucket.name
    source_key = urllib.parse.unquote_plus(sqs_rec.s3.get_object.key, encoding="utf-8")
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"].read().decode("utf-8"),
    )

    # extract the judgement contents
    text_content = extract_text_content(file_content)
    upload_contents(source_key, text_content)


def extract_text_content(file_content: DocumentAsXMLString) -> DocumentAsXMLString:
    """
    Extract text from the content elements of the XML file
    """
    return parse_file(file_content)


def upload_contents(source_key: str, text_content: DocumentAsXMLString):
    """
    Uploads text to S3 bucket
    """
    filename = os.path.splitext(source_key)[0] + ".txt"
    LOGGER.info("Uploading text content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    s3_obj = s3.Object(DEST_BUCKET, filename)
    s3_obj.put(Body=text_content)


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")


@event_source(data_class=S3Event)
def handler(event: S3Event, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Extract judgement contents from XML")
    LOGGER.info(DEST_BUCKET)
    try:
        LOGGER.info("SQS EVENT: %s", event)

        for sqs_rec in event.records:
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
