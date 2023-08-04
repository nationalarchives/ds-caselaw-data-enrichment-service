#!/usr/bin/env python3

import json
import logging
import os
import re

import boto3
from bs4 import BeautifulSoup

from replacer.make_replacments import split_text_by_closing_header_tag

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
    """
    Upload judgment to destination S3 bucket
    """
    filename = source_key

    LOGGER.info("Uploading text content to %s/%s", DEST_BUCKET, filename)
    s3 = boto3.resource("s3")
    object = s3.Object(DEST_BUCKET, filename)
    object.put(Body=text_content)


def detect_reference(text, etype):
    """
    Detect citation references.
    :param text: text to be searched for references
    :param etype: type of reference to be detected
    :returns references: List(Tuple[((start, end), detected_ref)]), of detected legislation
    """
    patterns = {
        "legislation": r"<ref(((?!ref>).)*)(.*?)ref>",
    }

    references = [(m.span(), m.group()) for m in re.finditer(patterns[etype], text)]
    return references


def sanitize_judgment(file_content):
    remove_from_judgment = []
    list_of_references = detect_reference(file_content, "legislation")
    for i in list_of_references:
        opening = i[1].split(">")[0] + ">"
        remove_from_judgment.append((opening, ""))
        remove_from_judgment.append(("</ref>", ""))

    for k, v in remove_from_judgment:
        file_content = file_content.replace(k, v)

    soup = BeautifulSoup(file_content, "xml")
    enriched_date = soup.find_all("FRBRdate", {"name": "tna-enriched"})
    if enriched_date:
        for i in enriched_date:
            i.decompose()
    engine_version = soup.find_all("uk:tna-enrichment-engine")
    if engine_version:
        for i in engine_version:
            i.decompose()

    soup_string = str(soup)

    return soup_string


def process_event(sqs_rec):
    """
    Isolating processing from event unpacking for portability and testing
    """
    s3_client = boto3.client("s3")

    message = json.loads(sqs_rec["body"])
    LOGGER.info("EVENT: %s", message)

    msg_attributes = sqs_rec["messageAttributes"]
    message["replacements"]
    source_key = msg_attributes["source_key"]["stringValue"]

    replacement_bucket = msg_attributes["source_bucket"]["stringValue"]
    LOGGER.info("Replacement bucket from message")
    LOGGER.info(replacement_bucket)

    LOGGER.info(REPLACEMENTS_BUCKET)
    LOGGER.info("Source_key")
    LOGGER.info(source_key)

    filename = os.path.splitext(source_key)[0] + ".xml"

    LOGGER.info(SOURCE_BUCKET)
    LOGGER.info("Filename")
    LOGGER.info(filename)

    file_content = (
        s3_client.get_object(Bucket=SOURCE_BUCKET, Key=filename)["Body"]
        .read()
        .decode("utf-8")
    )

    cleaned_file_content = sanitize_judgment(file_content)

    judgment_split = split_text_by_closing_header_tag(cleaned_file_content)

    print(judgment_split)

    LOGGER.info("Got original XML file content")
    LOGGER.info(REPLACEMENTS_BUCKET)
    replacement_file_content = (
        s3_client.get_object(Bucket=REPLACEMENTS_BUCKET, Key=source_key)["Body"]
        .read()
        .decode("utf-8")
    )

    LOGGER.info("Got replacement file content")

    # extract the judgement contents
    replaced_text_content = replace_text_content(
        judgment_split[2], replacement_file_content
    )
    LOGGER.info("Got replacement text content")
    print(replaced_text_content)

    # combine header with replaced text content before uploading to enriched bucket
    judgment_split[2] = replaced_text_content
    print(judgment_split[2])
    full_replaced_text_content = "".join(judgment_split)
    upload_contents(filename, full_replaced_text_content)


def replace_text_content(file_content, replacements_content):
    """
    Run the replacer pipeline to make replacements on caselaw, legislation and abbreviations
    """
    replacements = []

    replacement_tuples_case = []
    replacement_tuples_leg = []
    replacement_tuples_abb = []

    tuple_file = replacements_content
    LOGGER.info("tuple_file")
    print(tuple_file)
    LOGGER.info("---lines--")

    for line in tuple_file.splitlines():
        LOGGER.debug(line)
        replacements.append(json.loads(line))

    for i in replacements:
        key, value = list(i.items())[0]

        LOGGER.info("replacements")
        print(replacements)
        if key == "case":
            case_law_tuple = tuple(i["case"])
            replacement_tuples_case.append(case_law_tuple)

        elif key == "leg":
            leg_tuple = tuple(i["leg"])
            replacement_tuples_leg.append(leg_tuple)

        else:
            abb_tuple = tuple(i["abb"])
            replacement_tuples_abb.append(abb_tuple)

    LOGGER.info("Replacement caselaw")
    print(replacement_tuples_case)

    from replacer.replacer_pipeline import replacer_pipeline

    file_data_enriched = replacer_pipeline(
        file_content,
        replacement_tuples_case,
        replacement_tuples_leg,
        replacement_tuples_abb,
    )
    LOGGER.info("Judgment enriched")

    return file_data_enriched


DEST_BUCKET = validate_env_variable("DEST_BUCKET_NAME")
SOURCE_BUCKET = validate_env_variable("SOURCE_BUCKET_NAME")
REPLACEMENTS_BUCKET = validate_env_variable("REPLACEMENTS_BUCKET")


# make replacements
def handler(event, context):
    """
    Function called by the lambda to run the process event
    """
    LOGGER.info("Make replacements")
    LOGGER.info(DEST_BUCKET)
    LOGGER.info(SOURCE_BUCKET)
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
