#!/usr/bin/env python3

import logging
import json
import urllib.parse
import os
import boto3

from lxml import etree

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


# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec):
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
                sqs_rec["s3"]["object"]["key"], encoding="utf-8"
            )
    print("Input bucket name:", source_bucket)
    print("Input S3 key:", source_key)

    file_content = s3_client.get_object(
                Bucket=source_bucket, Key=source_key)["Body"].read()

    content_valid = validate_content(file_content)

def find_schema(schema_bucket, schema_key):
    s3_client = boto3.client("s3")
    schema_content = s3_client.get_object(
                Bucket=schema_bucket, Key=schema_key)["Body"].read()

    return schema_content

def load_schema(schema_content):
    parser = etree.XMLParser(dtd_validation=True)   
    xmlschema_doc = parser.parseString(schema_content)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    return xmlschema

def validate_content(file_content):
    parser = etree.XMLParser(dtd_validation=VALIDATE_USING_DTD) 
    parser.setContentHandler(ContentHandler(  ))
    xmldoc = parser.parseString(file_content)

    if VALIDATE_USING_SCHEMA:
        schema_bucket = validate_env_variable("SCHEMA_BUCKET_NAME")
        schema_key = validate_env_variable("SCHEMA_BUCKET_KEY")
    
        schema_content = find_schema(schema_bucket, schema_key)
        schema = load_schema(schema_content)
        schema.validate(xmldoc)

    return True


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
VALIDATE_USING_SCHEMA = validate_env_variable("VALIDATE_USING_SCHEMA")
VALIDATE_USING_DTD = validate_env_variable("VALIDATE_USING_DTD")

def handler(event, context):
    LOGGER.info("validate-judgement-contents")
    LOGGER.info(DEST_BUCKET)
    try:
        LOGGER.info('SQS EVENT: %s', event)
        # event structure and parsing logic varies if the lambda function is involved directly from an S3:put object vs reading from an SQS queue


        # Get the object from the event and show its content type
        # source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
        # source_key = urllib.parse.unquote_plus(
        #     event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        # )

        # print("Input bucket name:", source_bucket)
        # print("Input S3 key:", source_key)

        for sqs_rec in event['Records']:
            # TODO make the code adapt to a direct invocation vs reading from an SQS queue

            # stop the test notification event from breaking the parsing logic
            if 'Event' in sqs_rec.keys() and sqs_rec['Event'] == 's3:TestEvent':
                break
            process_event(sqs_rec)


    except Exception as exception:
        LOGGER.error('Exception: %s', exception)
        raise

