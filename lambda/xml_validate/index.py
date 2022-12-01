#!/usr/bin/env python3

import json
import logging
import os
import urllib.parse
from distutils.util import strtobool
from io import BytesIO, StringIO

import boto3
from lxml import etree

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def validate_env_variable(env_var_name):
    print(f"Getting the value of the environment variable: {env_var_name}")

    try:
        env_variable = os.environ[env_var_name]
    except KeyError:
        raise Exception(f"Please, set environment variable {env_var_name}")

    if not env_variable:
        raise Exception(f"Please, provide environment variable {env_var_name}")

    return env_variable


# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec):
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
        LOGGER.debug("content valid")
    else:
        LOGGER.error("content invalid")

    return content_valid, source_key


def find_schema(schema_bucket, schema_key):
    s3_client = boto3.client("s3")
    schema_content = s3_client.get_object(Bucket=schema_bucket, Key=schema_key)[
        "Body"
    ].read()

    return schema_content


def load_schema(schema_content):
    parser = etree.XMLParser(dtd_validation=False)
    xmlschema_doc = etree.parse(BytesIO(schema_content), parser)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    return xmlschema


def validate_content(file_content):
    LOGGER.info("VALIDATE_USING_DTD")
    LOGGER.info(VALIDATE_USING_DTD)

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


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
DEST_ERROR_TOPIC = validate_env_variable("DEST_ERROR_TOPIC_NAME")
DEST_TOPIC = validate_env_variable("DEST_TOPIC_NAME")
VALIDATE_USING_SCHEMA = strtobool(validate_env_variable("VALIDATE_USING_SCHEMA"))
VALIDATE_USING_DTD = strtobool(validate_env_variable("VALIDATE_USING_DTD"))


def handler(event, context):
    LOGGER.info("validate-judgement-contents")
    LOGGER.info(DEST_BUCKET)
    valid_content = False
    source_key = ""
    try:
        LOGGER.info("SQS EVENT: %s", event)

        for sqs_rec in event["Records"]:
            # stop the test notification event from breaking the parsing logic
            if "Event" in sqs_rec.keys() and sqs_rec["Event"] == "s3:TestEvent":
                break
            valid_content, source_key = process_event(sqs_rec)

    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
    finally:
        message = "content is valid for " + source_key
        topic = DEST_TOPIC

        if valid_content:
            LOGGER.debug("content is valid sending notification")

        else:
            message = "content is invalid for " + source_key
            LOGGER.error(message)
            topic = DEST_ERROR_TOPIC
            sns_client = boto3.client("sns")
            response = sns_client.publish(
                TargetArn=topic,
                Message=json.dumps({"default": message}),
                MessageStructure="json",
            )
