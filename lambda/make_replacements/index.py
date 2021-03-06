#!/usr/bin/env python3

import logging
import json
import urllib.parse
import os
import boto3
import re

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

def upload_contents(source_key, text_content):
    filename = source_key

    LOGGER.info('uploading text content to %s/%s', DEST_BUCKET, filename)
    s3 = boto3.resource('s3')
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=text_content)

# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec):
    s3_client = boto3.client("s3")

    message = json.loads(sqs_rec['body'])
    LOGGER.info('EVENT: %s', message)

    msg_attributes = sqs_rec['messageAttributes']
    replacements = message['replacements']
    source_key = msg_attributes['source_key']['stringValue']

    replacement_bucket = msg_attributes['source_bucket']['stringValue']
    LOGGER.info('replacement_bucket from message')
    LOGGER.info(replacement_bucket)

    LOGGER.info(REPLACEMENTS_BUCKET)
    LOGGER.info('source_key')
    LOGGER.info(source_key)

    filename = os.path.splitext(source_key)[0] + ".xml"

    LOGGER.info(SOURCE_BUCKET)
    LOGGER.info('filename')
    LOGGER.info(filename)

    file_content = s3_client.get_object(
                Bucket=SOURCE_BUCKET, Key=filename)["Body"].read().decode('utf-8')

    # split file_content into header and judgment to ensure replacements only occur in judgment body
    judgment_split = re.split('(</header>)',  file_content)
    
    LOGGER.info("got original xml file_content")
    LOGGER.info(REPLACEMENTS_BUCKET)
    replacement_file_content = s3_client.get_object(
                Bucket=REPLACEMENTS_BUCKET, Key=source_key)["Body"].read().decode('utf-8')
      
    LOGGER.info("got replacement file_content")

    # extract the judgement contents
    replaced_text_content = replace_text_content(judgment_split[2], replacement_file_content)
    LOGGER.info("got replacement text_content")

    # combine header with replaced text content before uploading to enriched bucket
    judgment_split[2] = replaced_text_content
    full_replaced_text_content = ''.join(judgment_split)
    upload_contents(filename, full_replaced_text_content)

def replace_text_content(file_content, replacements_content):
    replacements = []

    replacement_tuples_case = []
    replacement_tuples_leg = []
    replacement_tuples_abb = []

    tuple_file = replacements_content
    LOGGER.info('tuple_file')
    print(tuple_file)
    LOGGER.info('---lines--')

    for line in tuple_file.splitlines():
        LOGGER.debug(line)
        replacements.append(json.loads(line))

    for i in replacements:
        key, value = list(i.items())[0]

        LOGGER.info('replacements')
        print(replacements)
        if key == 'case':
            case_law_tuple = tuple(i['case'])
            replacement_tuples_case.append(case_law_tuple)

        elif key == 'leg':
            leg_tuple = tuple(i['leg'])
            replacement_tuples_leg.append(leg_tuple)

        else:
            abb_tuple = tuple(i['abb'])
            replacement_tuples_abb.append(abb_tuple)

    LOGGER.info('replacement_tuples_case')   
    print(replacement_tuples_case)

    from replacer.replacer import replacer_pipeline
    file_data_enriched = replacer_pipeline(file_content, replacement_tuples_case, replacement_tuples_leg, replacement_tuples_abb)
    LOGGER.info('file_data_enriched')

    return file_data_enriched

DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET_NAME")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")

# make replacements
# write to s3 which will trigger a message on an sqs queue
def handler(event, context):
    LOGGER.info("determine-replacements")
    LOGGER.info(DEST_BUCKET)
    LOGGER.info(SOURCE_BUCKET)
    try:
        LOGGER.info('SQS EVENT: %s', event)

        for sqs_rec in event['Records']:
            # stop the test notification event from breaking the parsing logic
            if 'Event' in sqs_rec.keys() and sqs_rec['Event'] == 's3:TestEvent':
                break
            process_event(sqs_rec)


    except Exception as exception:
        LOGGER.error('Exception: %s', exception)
        raise

