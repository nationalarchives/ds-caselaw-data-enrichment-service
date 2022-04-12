#!/usr/bin/env python3

from gc import garbage
import logging
import json
import sys
import urllib.parse
import os
import boto3
import random
from botocore.exceptions import ClientError
from dateutil.parser import parse as dparser

import spacy
from spacy.language import Language

LOGGER = logging.getLogger()
# LOGGER.setLevel(logging.INFO)
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

############################################
# CLASS HELPERS
############################################
class getLoginSecrets:
    def get_secret(self, aws_secret_name, aws_region_name):
        secret_name = aws_secret_name
        region_name = aws_region_name

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
        # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        # We rethrow the exception by default.

        try:
            LOGGER.info(" about to get_secret_value_response")
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            LOGGER.info("got_secret_value_response")

            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if "SecretString" in get_secret_value_response:
                secret = get_secret_value_response["SecretString"]
                LOGGER.info("got SecretString")
            else:
                LOGGER.info("not SecretString")
                decoded_binary_secret = base64.b64decode(
                    get_secret_value_response["SecretBinary"]
                )
                secret = decoded_binary_secret
            LOGGER.info("here")
            return secret
        # except ClientError as e:
        #     if e.response["Error"]["Code"] == "DecryptionFailureException":
        #         # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
        #         # Deal with the exception here, and/or rethrow at your discretion.
        #         raise e
        #     elif e.response["Error"]["Code"] == "InternalServiceErrorException":
        #         # An error occurred on the server side.
        #         # Deal with the exception here, and/or rethrow at your discretion.
        #         raise e
        #     elif e.response["Error"]["Code"] == "InvalidParameterException":
        #         # You provided an invalid value for a parameter.
        #         # Deal with the exception here, and/or rethrow at your discretion.
        #         raise e
        #     elif e.response["Error"]["Code"] == "InvalidRequestException":
        #         # You provided a parameter value that is not valid for the current state of the resource.
        #         # Deal with the exception here, and/or rethrow at your discretion.
        #         raise e
        #     elif e.response["Error"]["Code"] == "ResourceNotFoundException":
        #         # We can't find the resource that you asked for.
        #         # Deal with the exception here, and/or rethrow at your discretion.
        #         raise e
        # added as the validation exception was not being caught
        except Exception as exception:
            LOGGER.error('Exception: %s', exception)
            raise
        # else:

############################################
# - INSTANTIATE CLASS HELPERS
# - GET ENV VARIABLES
############################################
database_name = validate_env_variable("DATABASE_NAME")
table_name = validate_env_variable("TABLE_NAME")
username = validate_env_variable("USERNAME")
port = validate_env_variable("PORT")
host = validate_env_variable("HOSTNAME")
aws_secret_name = validate_env_variable("SECRET_PASSWORD_LOOKUP")
aws_region_name = validate_env_variable("REGION_NAME")

get_secret = getLoginSecrets()

# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec):
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
                sqs_rec["s3"]["object"]["key"], encoding="utf-8"
            )
    LOGGER.debug("Input bucket name:%s", source_bucket)
    LOGGER.debug("Input S3 key:%s", source_key)

    # fetch the judgement contents
    file_content = s3_client.get_object(
                # Bucket=source_bucket, Key=source_key)["Body"].read()
                Bucket=source_bucket, Key=source_key)["Body"].read().decode('utf-8')
                
    LOGGER.debug(file_content)
    LOGGER.debug("memory size =%d", sys.getsizeof(file_content))

    # fetch the rules
    rules_content = s3_client.get_object(
                Bucket=RULES_FILE_BUCKET, Key=RULES_FILE_KEY)["Body"].read()
    LOGGER.debug(rules_content)
    LOGGER.debug("memory size =%d", sys.getsizeof(file_content))

    replacements = determine_replacements(file_content, rules_content)
    LOGGER.debug("got replacements")
    replacements_encoded = write_replacements_file(replacements)
    LOGGER.debug("encoded replacements")
    LOGGER.debug(replacements_encoded)
    uploaded_key = upload_replacements(REPLACEMENTS_BUCKET, source_key, replacements_encoded)
    LOGGER.debug("uploaded replacements to %s", uploaded_key)
    push_contents(REPLACEMENTS_BUCKET, uploaded_key)
    LOGGER.debug("message sent on queue")

def write_replacements_file(replacement_list):
    tuple_file = ""
    for i in replacement_list:
        replacement_object = {"{}".format(type(i).__name__): list(i)}
        # json.dump(replacement_object, tuple_file)
        # tuple_file.write("\n")
        tuple_file += json.dumps(replacement_object)
        tuple_file += "\n"
    return tuple_file

def upload_replacements(replacements_bucket, replacements_key, replacements):
    LOGGER.info('uploading text content to %s/%s', replacements_bucket, replacements_key)
    s3 = boto3.resource('s3')
    object = s3.Object(replacements_bucket, replacements_key)
    object.put(Body=replacements)
    return object.key

def init_NLP():
    nlp = spacy.load("en_core_web_sm", exclude=['tok2vec', 'attribute_ruler', 'lemmatizer', 'ner'])
    
    from abbreviation_extraction.abbreviations import AbbreviationDetector
    # init the class - stateful pipeline component 
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(nlp, name: str): 
        return AbbreviationDetector(nlp)

    nlp.add_pipe("abbreviation_detector") 

    return nlp


def determine_replacements(file_content):
    # setup the spacy pipeline
    nlp = init_NLP()
    LOGGER.debug('got nlp')
    # attempt to free memory
    # del rules_content
    # import gc
    # gc.collect()
    # doc = nlp(file_content)
    doc = nlp(file_content)

    replacements = get_abbreviation_replacements(doc)
    LOGGER.debug('replacements identified')
    LOGGER.debug(len(replacements))

    return replacements

def get_abbreviation_replacements(doc):
    from abbreviation_extraction.abbreviations import abb_pipeline 

    replacements = abb_pipeline(doc)
    return replacements

def push_contents(uploaded_bucket, uploaded_key):
    # Get the queue
    sqs = boto3.resource('sqs')
    queue = sqs.Queue(DEST_QUEUE)

    # Create a new message
    message = {"replacements": uploaded_key}
    msg_attributes = {
        'source_key': {
            'DataType': 'String',
            'StringValue': uploaded_key
        },
        'source_bucket': {
            'DataType': 'String',
            'StringValue': uploaded_bucket
        }
    }
    # json.dumps({"rev":rev_,"s_ver_str":s_ver_str_,"pro": pro_ })
    response = queue.send_message(MessageBody=json.dumps(message), MessageAttributes=msg_attributes)

DEST_QUEUE = validate_env_variable("DEST_QUEUE_NAME")
RULES_FILE_BUCKET = validate_env_variable("RULES_FILE_BUCKET")
RULES_FILE_KEY = validate_env_variable("RULES_FILE_KEY")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")

def handler(event, context):
    LOGGER.info("determine-replacements")
    LOGGER.info(DEST_QUEUE)
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

