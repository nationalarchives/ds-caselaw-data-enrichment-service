import datetime
import logging
import urllib.parse

import boto3
from aws_lambda_powertools.utilities.data_classes import S3Event, event_source
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from bs4 import BeautifulSoup

from legislation_provisions_extraction.legislation_provisions import (
    provisions_pipeline,
)
from replacer.second_stage_replacer import replace_references_by_paragraph
from utils.custom_types import DocumentAsXMLString
from utils.environment_helpers import validate_env_variable

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class SourceXMLMissingElement(RuntimeError):
    """The provided XML document is missing an expected element, and we are choosing to fail."""


def upload_contents(source_key: str, output_file_content: DocumentAsXMLString) -> None:
    """
    Upload enriched file to S3 bucket
    """
    LOGGER.info("Uploading enriched file to %s/%s", DEST_BUCKET, source_key)
    s3 = boto3.resource("s3")
    s3_obj = s3.Object(DEST_BUCKET, source_key)
    s3_obj.put(Body=output_file_content)


def add_timestamp_and_engine_version(
    file_data: DocumentAsXMLString,
) -> DocumentAsXMLString:
    """
    Add today's timestamp and version at time of enrichment
    """
    soup = BeautifulSoup(file_data, "xml")
    today = datetime.datetime.now(tz=datetime.UTC)
    today_str = today.strftime("%Y-%m-%dT%H:%M:%S")
    enriched_date = soup.new_tag(f'FRBRdate date="{today_str}" name="tna-enriched"')
    enrichment_version = soup.new_tag(
        "uk:tna-enrichment-engine",
        attrs={"xmlns:uk": "https://caselaw.nationalarchives.gov.uk/akn"},
    )
    enrichment_version.string = "7.2.2"

    if not soup.proprietary:
        msg = "This document does not have a <proprietary> element."
        raise SourceXMLMissingElement(msg)

    soup.proprietary.append(enrichment_version)

    if not soup.FRBRManifestation or not soup.FRBRManifestation.FRBRdate:
        msg = "This document does not already have a manifestation date."
        raise SourceXMLMissingElement(msg)

    soup.FRBRManifestation.FRBRdate.insert_after(enriched_date)

    return DocumentAsXMLString(str(soup))


def process_event(sqs_rec: S3EventRecord) -> None:
    """
    Function to fetch the XML, call the legislation provisions extraction pipeline and upload the enriched XML to the
    destination bucket
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec.s3.bucket.name
    source_key = urllib.parse.unquote_plus(sqs_rec.s3.get_object.key, encoding="utf-8")
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"].read().decode("utf-8"),
    )

    resolved_refs = provisions_pipeline(file_content)
    print(resolved_refs)

    if resolved_refs:
        soup = BeautifulSoup(file_content, "xml")
        output_file_data = replace_references_by_paragraph(soup, resolved_refs)
        timestamp_added = add_timestamp_and_engine_version(output_file_data)
        upload_contents(source_key, timestamp_added)
    else:
        timestamp_added = add_timestamp_and_engine_version(file_content)
        upload_contents(source_key, timestamp_added)


DEST_BUCKET = validate_env_variable("DEST_BUCKET")


@event_source(data_class=S3Event)
def handler(event: S3Event, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("detect-legislation-provisions")
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
