#!/usr/bin/env python3

import csv
import json
import logging
import os
import random
import sys
import urllib.parse
from gc import garbage

import boto3
import spacy
from botocore.exceptions import ClientError
from dateutil.parser import parse as dparser
from spacy.language import Language

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def validate_env_variable(env_var_name):
    LOGGER.debug(f"Getting the value of the environment variable: {env_var_name}")

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
    message = json.loads(sqs_rec["body"])
    LOGGER.info("EVENT: %s", message)
    msg_attributes = sqs_rec["messageAttributes"]
    replacements = message["replacements"]
    source_key = msg_attributes["source_key"]["stringValue"]

    source_bucket = msg_attributes["source_bucket"]["stringValue"]
    LOGGER.info("replacement_bucket from message")
    LOGGER.info(source_bucket)

    LOGGER.debug("Input bucket name:%s", source_bucket)
    LOGGER.debug("Input S3 key:%s", source_key)

    # fetch the judgement contents
    file_content = (
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )

    LOGGER.debug(file_content)
    LOGGER.debug("memory size =%d", sys.getsizeof(file_content))

    replacements = determine_replacements(file_content)
    LOGGER.debug("got replacements")
    replacements_encoded = write_replacements_file(replacements)
    LOGGER.debug("encoded replacements")
    LOGGER.debug(replacements_encoded)

    # open and read existing file from s3 bucket
    replacements_content = (
        s3_client.get_object(Bucket=REPLACEMENTS_BUCKET, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )
    replacements_encoded = replacements_content + replacements_encoded

    uploaded_key = upload_replacements(
        REPLACEMENTS_BUCKET, source_key, replacements_encoded
    )
    LOGGER.debug("uploaded replacements to %s", uploaded_key)
    push_contents(REPLACEMENTS_BUCKET, source_key)
    LOGGER.debug("message sent on queue")


def write_replacements_file(replacement_list):
    tuple_file = ""
    for i in replacement_list:
        replacement_object = {"{}".format(type(i).__name__): list(i)}
        tuple_file += json.dumps(replacement_object)
        tuple_file += "\n"
    return tuple_file


def upload_replacements(replacements_bucket, replacements_key, replacements):
    s3 = boto3.resource("s3")
    object = s3.Object(replacements_bucket, replacements_key)
    object.put(Body=replacements)


def determine_replacements(file_content):
    replacements = get_abbreviation_replacements(file_content)

    return replacements


def get_abbreviation_replacements(file_content):
    from abbreviation_extraction.abbreviations_matcher import abb_pipeline

    nlp = init_NLP()
    replacements = abb_pipeline(file_content, nlp)

    return replacements


def init_NLP():
    nlp = spacy.load(
        "en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"]
    )
    nlp.max_length = 2500000
    return nlp


def push_contents(uploaded_bucket, uploaded_key):
    # Get the queue
    sqs = boto3.resource("sqs")
    queue = sqs.Queue(DEST_QUEUE)

    # Create a new message
    message = {"replacements": uploaded_key}
    msg_attributes = {
        "source_key": {"DataType": "String", "StringValue": uploaded_key},
        "source_bucket": {"DataType": "String", "StringValue": uploaded_bucket},
    }
    response = queue.send_message(
        MessageBody=json.dumps(message), MessageAttributes=msg_attributes
    )


DEST_QUEUE = validate_env_variable("DEST_QUEUE_NAME")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")


def handler(event, context):
    LOGGER.info("determine-replacements")
    LOGGER.info(DEST_QUEUE)
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
