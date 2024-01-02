#!env/bin/python

import json
import logging
import urllib.parse
from io import StringIO

import boto3
import pandas as pd
import spacy
from aws_lambda_powertools.utilities.data_classes import S3Event, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext

from utils.initialise_db import init_db_engine

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def write_patterns_file(patterns_list: str) -> str:
    """
    Write patterns to separate lines
    """
    patterns_file = ""
    for pattern in patterns_list:
        patterns_file += pattern + "\n"
    return patterns_file


def upload_replacements(
    pattern_bucket: str, pattern_key: str, patterns_file: str
) -> str:
    """
    Upload replacements to S3 bucket
    """
    LOGGER.info("Uploading text content to %s/%s", pattern_bucket, pattern_key)
    s3 = boto3.resource("s3")
    object = s3.Object(pattern_bucket, pattern_key)
    object.put(Body=patterns_file)
    return object.key


def create_test_jsonl(source_bucket: str, df: pd.DataFrame) -> None:
    """
    Create test jsonl of patterns pulled from a csv
    """
    patterns = df["pattern"].tolist()
    patterns_file = write_patterns_file(patterns)
    upload_replacements(source_bucket, "test_citation_patterns.jsonl", patterns_file)


def test_manifest(df: pd.DataFrame, patterns: list[str]) -> None:
    """
    Test for the rules manifest.
    """
    nlp = spacy.load(
        "en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"]
    )
    nlp.max_length = 2500000

    citation_ruler = nlp.add_pipe("entity_ruler")
    citation_ruler.add_patterns(patterns)

    examples = df["match_example"].tolist()

    MATCHED_IDS = []

    for example in examples:
        doc = nlp(example)
        ent = [str(ent.ent_id_) for ent in doc.ents][0]
        MATCHED_IDS.append(ent)

    MATCHED_IDS = list(set(MATCHED_IDS))
    print(len(MATCHED_IDS), df.shape[0])
    assert len(MATCHED_IDS) == df.shape[0]


@event_source(data_class=S3Event)
def lambda_handler(event: S3Event, context: LambdaContext) -> None:
    """
    Function called by the lambda to update the rules
    """
    LOGGER.info("Updating case law detection rules")

    # read CSV file from rules bucket
    s3 = boto3.client("s3")
    event_record = event.record
    source_bucket = event_record.s3.bucket.name
    source_key = urllib.parse.unquote_plus(
        event_record.s3.get_object.key, encoding="utf-8"
    )
    print(source_bucket)
    print(source_key)
    if source_key.endswith(".csv"):
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        csv_file = response["Body"].read().decode("utf-8")
        df = pd.read_csv(StringIO(csv_file))

        create_test_jsonl(source_bucket, df)
        jsonl_key = "test_citation_patterns.jsonl"

        patterns_resp = s3.get_object(Bucket=source_bucket, Key=jsonl_key)
        patterns = patterns_resp["Body"]
        pattern_list = [json.loads(line) for line in patterns.iter_lines()]

        try:
            test_manifest(df, pattern_list)
        except AssertionError:
            LOGGER.error("Exception: Manifest test failed")
            raise

        try:
            # write new jsonl file
            new_patterns_file = write_patterns_file(df["pattern"].to_list())
            upload_replacements(
                source_bucket, "citation_patterns.jsonl", new_patterns_file
            )

            # connect to database
            engine = init_db_engine()
            LOGGER.info("Engine created")

            # push rules to database --> if_exists="replace" as we're pushing full ruleset
            df.to_sql("manifest", engine, if_exists="replace", index=False)

            # dispose of engine
            engine.dispose()
            LOGGER.info("Rules updated")

        except Exception as exception:
            LOGGER.error("Exception: %s", exception)
            raise
