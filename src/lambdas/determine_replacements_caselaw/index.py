#!/usr/bin/env python3

import base64
import json
import logging
import os
import urllib.parse

import boto3
import spacy

from database import db_connection

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


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
        """
        Get login secrets for database access
        """
        secret_name = aws_secret_name
        region_name = aws_region_name

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region_name)

        try:
            LOGGER.info(" about to get_secret_value_response")
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            LOGGER.info("got_secret_value_response")

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
        except Exception as exception:
            LOGGER.error("Exception: %s", exception)
            raise


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
    """
    Function to fetch the XML, call the determine_replacements_caselaw pipeline and upload the enriched XML to the
    destination bucket
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
        sqs_rec["s3"]["object"]["key"], encoding="utf-8"
    )
    LOGGER.info("Input bucket name:%s", source_bucket)
    LOGGER.info("Input S3 key:%s", source_key)

    # fetch the judgement contents
    file_content = (
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )

    # fetch the rules
    rules_content = s3_client.get_object(Bucket=RULES_FILE_BUCKET, Key=RULES_FILE_KEY)[
        "Body"
    ].read()

    replacements = determine_replacements(file_content, rules_content)
    LOGGER.info("Detected citations and built replacements")
    print(replacements)
    replacements_encoded = write_replacements_file(replacements)
    LOGGER.info("Wrote replacements to file")
    uploaded_key = upload_replacements(
        REPLACEMENTS_BUCKET, source_key, replacements_encoded
    )
    LOGGER.info("Uploaded replacements to %s", uploaded_key)

    push_contents(source_bucket, source_key)
    LOGGER.info(
        "Message sent on queue to start determine-replacements-legislation lambda"
    )


def write_replacements_file(replacement_list):
    """
    Writes tuples of abbreviations and long forms from a list of replacements
    """
    tuple_file = ""
    for i in replacement_list:
        replacement_object = {"{}".format(type(i).__name__): list(i)}
        tuple_file += json.dumps(replacement_object)
        tuple_file += "\n"
    return tuple_file


def upload_replacements(replacements_bucket, replacements_key, replacements):
    """
    Uploads replacements to S3 bucket
    """
    LOGGER.info(
        "Uploading text content to %s/%s", replacements_bucket, replacements_key
    )
    s3 = boto3.resource("s3")
    object = s3.Object(replacements_bucket, replacements_key)
    object.put(Body=replacements)
    return object.key


def init_NLP(rules_content):
    """
    Load spacy model and add rules from pre-defined patterns list
    """
    nlp = spacy.load(
        "en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"]
    )
    nlp.max_length = 5000000
    LOGGER.info("Loading citation patterns jsonl")

    s3 = boto3.client("s3")
    patterns_resp = s3.get_object(Bucket=RULES_FILE_BUCKET, Key=RULES_FILE_KEY)
    patterns = patterns_resp["Body"]
    pattern_list = [json.loads(line) for line in patterns.iter_lines()]

    citation_ruler = nlp.add_pipe("entity_ruler")
    citation_ruler.add_patterns(pattern_list)

    # LOGGER.info("checking file system access")
    # from os import listdir
    # from os.path import isfile, join

    # # mypath = '/var/task'
    # # onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    # # print(onlyfiles)
    # # print(os.path.exists('/var/task/caselaw_extraction/rules/citation_patterns.jsonl'))
    # # rule_file_name = 'citation_patterns.jsonl'
    # # rule_file_path = '/var/task/' + rule_file_name
    # # print(os.path.exists(rule_file_path))
    # # # hack to avoid using from disk is to overwrite the local file with the latest version from s3
    # # new_filename = '/tmp/'+rule_file_name
    # # newFile = open(new_filename,'wb')
    # # newFile.write(rules_content)
    # # LOGGER.debug(os.path.exists(new_filename))
    # # citation_ruler = nlp.add_pipe("entity_ruler").from_disk('/var/task/caselaw_extraction/rules/citation_patterns.jsonl')
    # # citation_ruler = nlp.add_pipe("entity_ruler").from_disk('/var/task/citation_patterns.jsonl')
    # # citation_ruler = nlp.add_pipe("entity_ruler").from_disk(new_filename)
    # # citation_ruler = nlp.add_pipe("entity_ruler").from_bytes(rules_content)
    return nlp


def init_DB():
    """
    Establish database connection
    """
    password = get_secret.get_secret(aws_secret_name, aws_region_name)
    db_conn = db_connection.create_connection(
        database_name, username, password, host, port
    )
    return db_conn


def close_connection(db_conn):
    """
    Close the database connection
    """
    db_connection.close_connection(db_conn)


def determine_replacements(file_content, rules_content):
    """
    Fetch caselaw replacements from database
    """
    # connect to the database
    db_conn = init_DB()

    # setup the spacy pipeline
    nlp = init_NLP(rules_content)
    LOGGER.info("Loaded NLP model")
    doc = nlp(file_content)

    replacements = get_caselaw_replacements(doc, db_conn)
    LOGGER.info("Replacements identified")
    LOGGER.info(len(replacements))
    close_connection(db_conn)

    return replacements


def get_caselaw_replacements(doc, db_conn):
    """
    Run the caselaw pipeline on the document
    """
    from caselaw_extraction.caselaw_matcher import case_pipeline

    replacements = case_pipeline(doc, db_conn)
    return replacements


def push_contents(uploaded_bucket, uploaded_key):
    """
    Delivers replacements to the specified queue
    """
    # Get the queue
    sqs = boto3.resource("sqs")
    queue = sqs.Queue(DEST_QUEUE)

    # Create a new message
    message = {"replacements": uploaded_key}
    msg_attributes = {
        "source_key": {"DataType": "String", "StringValue": uploaded_key},
        "source_bucket": {"DataType": "String", "StringValue": uploaded_bucket},
    }
    queue.send_message(
        MessageBody=json.dumps(message), MessageAttributes=msg_attributes
    )


DEST_QUEUE = validate_env_variable("DEST_QUEUE_NAME")
RULES_FILE_BUCKET = validate_env_variable("RULES_FILE_BUCKET")
RULES_FILE_KEY = validate_env_variable("RULES_FILE_KEY")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")


def handler(event, context):
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Determine caselaw replacements")
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