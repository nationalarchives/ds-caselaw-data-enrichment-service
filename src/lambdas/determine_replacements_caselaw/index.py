#!/usr/bin/env python3

import json
import logging
import urllib.parse
from typing import TYPE_CHECKING

import boto3
import spacy
from aws_lambda_powertools.utilities.data_classes import S3Event, event_source
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from utils.environment_helpers import validate_env_variable
from utils.initialise_db import init_db_connection
from utils.types import DocumentAsXMLString

if TYPE_CHECKING:
    from mypy_boto3_sqs.type_defs import MessageAttributeValueQueueTypeDef

# This is horrid, but we're copying database.py to a different folder
# to where it is within the repo within the install script.
if TYPE_CHECKING:
    from ..database import db_connection
else:
    from database import db_connection


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec: S3EventRecord) -> None:
    """
    Function to fetch the XML, call the determine_replacements_caselaw pipeline and upload the enriched XML to the
    destination bucket
    """
    s3_client = boto3.client("s3")
    source_bucket = sqs_rec.s3.bucket.name
    source_key = urllib.parse.unquote_plus(sqs_rec.s3.get_object.key, encoding="utf-8")
    LOGGER.info("Input bucket name:%s", source_bucket)
    LOGGER.info("Input S3 key:%s", source_key)

    # fetch the judgement contents
    file_content = DocumentAsXMLString(
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


def upload_replacements(
    replacements_bucket: str, replacements_key: str, replacements: str
) -> str:
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
    db_conn = init_db_connection()

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
    msg_attributes: dict[str, MessageAttributeValueQueueTypeDef] = {
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


@event_source(data_class=S3Event)
def handler(event: S3Event, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Determine caselaw replacements")
    LOGGER.info(DEST_QUEUE)
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
