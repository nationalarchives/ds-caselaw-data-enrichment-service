#!env/bin/python

import base64
import json
import logging
import os
import urllib.parse
from io import StringIO

import boto3
import pandas as pd
import spacy
from psycopg2 import Error
from sqlalchemy import create_engine

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


def write_patterns_file(patterns_list):
    """
    Write patterns to seperate lines
    """
    patterns_file = ""
    for pattern in patterns_list:
        patterns_file += pattern + "\n"
    return patterns_file


def upload_replacements(pattern_bucket, pattern_key, patterns_file):
    """
    Upload replacements to S3 bucket
    """
    LOGGER.info("Uploading text content to %s/%s", pattern_bucket, pattern_key)
    s3 = boto3.resource("s3")
    object = s3.Object(pattern_bucket, pattern_key)
    object.put(Body=patterns_file)
    return object.key


def create_test_jsonl(source_bucket, df):
    """
    Create test jsonl of patterns pulled from a csv
    """
    patterns = df["pattern"].tolist()
    patterns_file = write_patterns_file(patterns)
    upload_replacements(source_bucket, "test_citation_patterns.jsonl", patterns_file)


def test_manifest(df, patterns):
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


def lambda_handler(event, context):
    """
    Function called by the lambda to update the rules
    """
    LOGGER.info("Updating case law detection rules")

    # get password for database
    password = get_secret.get_secret(aws_secret_name, aws_region_name)

    # read CSV file from rules bucket
    s3 = boto3.client("s3")
    source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    print(source_bucket)
    print(source_key)
    if source_key.endswith(".csv"):
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        csv_file = response["Body"].read().decode("utf-8")
        df = pd.read_csv(StringIO(csv_file))
        # print(df)

        create_test_jsonl(source_bucket, df)
        jsonl_key = "test_citation_patterns.jsonl"

        patterns_resp = s3.get_object(Bucket=source_bucket, Key=jsonl_key)
        patterns = patterns_resp["Body"]
        pattern_list = [json.loads(line) for line in patterns.iter_lines()]

        try:
            test_manifest(df, pattern_list)

            # write new jsonl file
            new_patterns_file = write_patterns_file(df["pattern"].to_list())
            upload_replacements(
                source_bucket, "citation_patterns.jsonl", new_patterns_file
            )

            # connect to database
            try:
                engine = create_engine(
                    f"postgresql://{username}:{password}@{host}:{port}/{database_name}"
                )
                LOGGER.info("Engine created")

                # push rules to database --> if_exists="replace" as we're pushing full ruleset
                df.to_sql("manifest", engine, if_exists="replace", index=False)

                # dispose of engine
                engine.dispose()
                LOGGER.info("Rules updated")

            except (Exception, Error) as error:
                LOGGER.error("Error while connecting to PostgreSQL", error)
        except AssertionError:
            LOGGER.error("Manifest test failed")
            raise
