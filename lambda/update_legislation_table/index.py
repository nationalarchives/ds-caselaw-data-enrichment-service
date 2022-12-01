#!env/bin/python

import datetime
import logging
import os
import re
from io import BytesIO

import boto3
import pandas as pd
import psycopg2 as pg
from botocore.exceptions import ClientError
from psycopg2 import Error
from SPARQLWrapper import CSV, SPARQLWrapper
from sqlalchemy import create_engine

# import awswrangler.secretsmanager as awssm

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
            LOGGER.error("Exception: %s", exception)
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

sparql_username = validate_env_variable("SPARQL_USERNAME")
sparql_password = validate_env_variable("SPARQL_PASSWORD")

get_secret = getLoginSecrets()


def get_leg_update(sparql_username, sparql_password, days=7):
    # date = pd.to_datetime(date)
    today = datetime.datetime.today()
    date = today - datetime.timedelta(days)

    sparql = SPARQLWrapper("https://www.legislation.gov.uk/sparql")
    sparql.setCredentials(user=sparql_username, passwd=sparql_password)
    sparql.setReturnFormat(CSV)
    df = pd.DataFrame()
    sparql.setQuery(
        """
                prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                prefix xsd: <http://www.w3.org/2001/XMLSchema#>
                prefix void: <http://rdfs.org/ns/void#>
                prefix dct: <http://purl.org/dc/terms/>
                prefix sd: <http://www.w3.org/ns/sparql-service-description#>
                prefix prov: <http://www.w3.org/ns/prov#>
                prefix leg: <http://www.legislation.gov.uk/def/legislation/>
                select distinct ?ref  ?title ?ref_version ?shorttitle ?citation ?acronymcitation 
                where {
                   ?activity prov:endedAtTime ?actTime .
                   ?graph prov:wasInfluencedBy ?activity .
                   ?activity rdf:type <http://www.legislation.gov.uk/def/provenance/Addition> .
                   ?dataUnitDataSet sd:namedGraph ?graph .
                   <http://www.legislation.gov.uk/id/dataset/topic/core> void:subset ?dataUnitDataSet .
                   graph ?graph { ?ref a leg:Legislation; a leg:UnitedKingdomPublicGeneralAct ;
                                        leg:title ?title ;
                                        leg:interpretation ?version .
                                   OPTIONAL { ?ref leg:citation ?citation  } . 
                                   OPTIONAL {?ref leg:acronymCitation ?acronymcitation} .
                                   OPTIONAL {?ref_version   leg:shortTitle ?shorttitle} .}
                   FILTER(str(?actTime) > "%s")
                }
                """
        % date
    )
    results = sparql.query().convert()
    df = pd.read_csv(BytesIO(results))
    stitles = ["shorttitle", "citation", "acronymcitation"]
    df["candidate_titles"] = df[stitles].apply(list, axis=1)
    df = df.explode("candidate_titles")
    df = df[~df["candidate_titles"].isna()].drop_duplicates("candidate_titles")
    df["for_fuzzy"] = df.candidate_titles.apply(
        lambda x: re.search(r"Act\s+(\d{4})", x) != None
    )
    return df


def handler(event, context):
    LOGGER.info("update legislation database")

    password = get_secret.get_secret(aws_secret_name, aws_region_name)

    try:
        engine = create_engine(
            f"postgresql://{username}:{password}@{host}:{port}/{database_name}"
        )
        LOGGER.info("engine created")

        print("Trigger Date: ", event["trigger_date"])

        if "trigger_date" in event:
            trigger_date = event["trigger_date"]
            if type(trigger_date) == int:
                df = get_leg_update(sparql_username, sparql_password, trigger_date)
                print(df)
                df.to_sql("ukpga_lookup", engine, if_exists="append", index=False)
            else:
                df = get_leg_update(sparql_username, sparql_password)
                print(df)
                df.to_sql("ukpga_lookup", engine, if_exists="append", index=False)

        engine.dispose()
        LOGGER.info("legislation updated")

    except (Exception, Error) as error:
        LOGGER.error("Error while connecting to PostgreSQL", error)
