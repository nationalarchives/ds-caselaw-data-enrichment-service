#!/usr/bin/env python3

import json
import logging
import urllib.parse
from io import BytesIO

import boto3
from lxml import etree

from utils.environment_helpers import validate_env_variable

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

client = boto3.client("ssm")


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

    file_content = s3_client.get_object(Bucket=source_bucket, Key=source_key)[
        "Body"
    ].read()

    content_valid = validate_content(file_content)
    if content_valid:
        LOGGER.info("content valid")
    else:
        LOGGER.error("content invalid")

    return content_valid, source_key, file_content, source_bucket


def find_schema(schema_bucket, schema_key):
    """
    Fetch schema from the schema S3 bucket
    """
    s3_client = boto3.client("s3")
    schema_content = s3_client.get_object(Bucket=schema_bucket, Key=schema_key)[
        "Body"
    ].read()

    return schema_content


def load_schema(schema_content):
    """
    Parse the schema to XML schema to describe structure of XML document
    """
    parser = etree.XMLParser(dtd_validation=False)
    xmlschema_doc = etree.parse(BytesIO(schema_content), parser)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    return xmlschema


def validate_content(file_content):
    """
    Function to validate schema
    """
    LOGGER.info("VALIDATE USING SCHEMA")
    LOGGER.info(VALIDATE_USING_SCHEMA)

    parser = etree.XMLParser(dtd_validation=False)
    xmldoc = etree.parse(BytesIO(file_content), parser)
    result = True
    if VALIDATE_USING_SCHEMA:
        schema_bucket = validate_env_variable("SCHEMA_BUCKET_NAME")
        schema_key = validate_env_variable("SCHEMA_BUCKET_KEY")

        schema_content = find_schema(schema_bucket, schema_key)
        schema = load_schema(schema_content)
        result = schema.validate(xmldoc)

    return result


def upload_to_vcite(source_key, text_content):
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key

    LOGGER.info("Uploading text content to %s/%s", VCITE_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(VCITE_BUCKET, filename)
    object.put(Body=text_content)


def trigger_push_enriched(uploaded_bucket, uploaded_key):
    """
    Delivers replacements to the specified queue
    """
    # Get the queue
    sqs = boto3.resource("sqs")
    queue = sqs.Queue(DEST_QUEUE)

    # Create a new message
    message = {"Validated": uploaded_key}
    msg_attributes = {
        "source_key": {"DataType": "String", "StringValue": uploaded_key},
        "source_bucket": {"DataType": "String", "StringValue": uploaded_bucket},
    }
    queue.send_message(
        MessageBody=json.dumps(message), MessageAttributes=msg_attributes
    )


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
VCITE_BUCKET = validate_env_variable("VCITE_BUCKET")
VCITE_ENRICHED_BUCKET = validate_env_variable("VCITE_ENRICHED_BUCKET")
DEST_ERROR_TOPIC = validate_env_variable("DEST_ERROR_TOPIC_NAME")
DEST_TOPIC = validate_env_variable("DEST_TOPIC_NAME")
VALIDATE_USING_SCHEMA = bool(int(validate_env_variable("VALIDATE_USING_SCHEMA")))
DEST_QUEUE = validate_env_variable("DEST_QUEUE")


def handler(event, context):
    """
    Function called by lambda to validate schema
    """
    LOGGER.info("Validate enriched judgement XML")
    LOGGER.info(DEST_BUCKET)

    parameter = client.get_parameter(Name="vCite", WithDecryption=True)
    # print(parameter)
    parameter_value = parameter["Parameter"]["Value"]
    print("vCite configuration:", parameter["Parameter"]["Value"])

    valid_content = False
    source_key = ""
    try:
        LOGGER.info("SQS EVENT: %s", event)

        for sqs_rec in event["Records"]:
            # stop the test notification event from breaking the parsing logic
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            valid_content, source_key, file_content, source_bucket = process_event(
                sqs_rec
            )

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
    finally:
        message = "content is valid for " + source_key
        topic = DEST_TOPIC

        if valid_content:
            LOGGER.info("Content is valid. Sending notification.")

            if parameter_value == "off":
                trigger_push_enriched(DEST_BUCKET, source_key)
                LOGGER.info("Message sent on queue to start push-enriched-xml lambda")
            else:
                if (
                    source_bucket
                    == "staging-tna-s3-tna-sg-xml-third-phase-enriched-bucket"
                ):
                    upload_to_vcite(source_key, file_content)
                else:
                    trigger_push_enriched(VCITE_ENRICHED_BUCKET, source_key)
                    LOGGER.info(
                        "Message sent on queue to start push-enriched-xml lambda"
                    )

        else:
            message = "Content is invalid for " + source_key
            LOGGER.info(message)
            topic = DEST_ERROR_TOPIC
            sns_client = boto3.client("sns")
            sns_client.publish(
                TargetArn=topic,
                Message=json.dumps({"default": message}),
                MessageStructure="json",
            )
