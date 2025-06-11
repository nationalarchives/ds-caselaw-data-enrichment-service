import json
import logging
from typing import TYPE_CHECKING

import boto3
import spacy
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from abbreviation_extraction.abbreviations_matcher import abb_pipeline
from utils.custom_types import Abbreviation, DocumentAsXMLString
from utils.environment_helpers import validate_env_variable

if TYPE_CHECKING:
    from mypy_boto3_sqs.type_defs import MessageAttributeValueTypeDef

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


# isolating processing from event unpacking for portability and testing
def process_event(sqs_rec: SQSRecord) -> None:
    """
    Function to fetch the XML, call the replacements abbreviations pipeline and upload the enriched XML to the
    destination bucket
    """
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
    file_content = DocumentAsXMLString(
        s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"].read().decode("utf-8"),
    )

    replacements = determine_replacements(file_content)
    print(replacements)
    replacements_encoded = encode_replacements_to_string(replacements)

    # open and read existing file from s3 bucket
    replacements_content = (
        s3_client.get_object(Bucket=REPLACEMENTS_BUCKET, Key=source_key)["Body"].read().decode("utf-8")
    )
    replacements_encoded = replacements_content + replacements_encoded

    upload_replacements(REPLACEMENTS_BUCKET, source_key, replacements_encoded)
    LOGGER.info("Uploaded replacements to %s", REPLACEMENTS_BUCKET)
    push_contents(REPLACEMENTS_BUCKET, source_key)
    LOGGER.info("Message sent on queue to start make-replacements lambda")


def encode_replacements_to_string(replacement_list: list[Abbreviation]) -> str:
    """
    Writes tuples of abbreviations and long forms from a list of replacements
    """
    tuple_file = ""
    for i in replacement_list:
        replacement_object = {f"{type(i).__name__}": list(i)}
        tuple_file += json.dumps(replacement_object)
        tuple_file += "\n"
    return tuple_file


def upload_replacements(replacements_bucket: str, replacements_key: str, replacements: str) -> None:
    """
    Uploads replacements to S3 bucket
    """
    s3 = boto3.resource("s3")
    s3_obj = s3.Object(replacements_bucket, replacements_key)
    s3_obj.put(Body=replacements)


def determine_replacements(file_content: str) -> list[Abbreviation]:
    """
    Calls abbreviation function to return abbreviation and long form
    """
    replacements = get_abbreviation_replacements(file_content)

    return replacements


def get_abbreviation_replacements(file_content: str) -> list[Abbreviation]:
    """
    Calls abbreviation pipeline to return abbreviation and long form
    """

    nlp = init_NLP()
    replacements = abb_pipeline(file_content, nlp)

    return replacements


def init_NLP():
    """
    Load spacy model
    """
    nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"])
    nlp.max_length = 2500000
    return nlp


def push_contents(uploaded_bucket: str, uploaded_key: str) -> None:
    """
    Delivers replacements to the specified queue
    """
    # Get the queue
    sqs = boto3.resource("sqs")
    queue = sqs.Queue(DEST_QUEUE)

    # Create a new message
    message = {"replacements": uploaded_key}
    msg_attributes: dict[str, MessageAttributeValueTypeDef] = {
        "source_key": {"DataType": "String", "StringValue": uploaded_key},
        "source_bucket": {"DataType": "String", "StringValue": uploaded_bucket},
    }
    queue.send_message(MessageBody=json.dumps(message), MessageAttributes=msg_attributes)


DEST_QUEUE = validate_env_variable("DEST_QUEUE_NAME")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context: LambdaContext) -> None:
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Determine abbreviations")
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
