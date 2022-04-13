#!env/bin/python

import json 
import os 
import random
import logging
import psycopg2 as pg
import boto3
from botocore.exceptions import ClientError
from dateutil.parser import parse as dparser
from psycopg2 import Error
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

# read rules from db and write to s3
def handler(event, context): 
    password = get_secret.get_secret(aws_secret_name, aws_region_name)
    LOGGER.info("password length %d", len(password))
    cxn = None
    csr = None

    try:
        cxn = pg.connect( user=username, 
                    password=password, 
                    host=host, 
                    port=port, 
                    database=database_name)

        LOGGER.info('connected to db')
        # query_create_table = f"create table {table_name} ( ix serial primary key, names varchar(50) unique not null );"
        # LOGGER.info('created table')
        # query_insert_data = f"insert into {table_name} (city) values ('Washington'), ('Philadelphia'), ('New York'), ('Chicago'), ('Los Angeles'), ('Seattle'), ('Portland'), ('Dallas'), ('Miami'), ('Charlotte');"
        # LOGGER.info('inserted in table')

        query_create_table = """CREATE TABLE IF NOT EXISTS "manifest" (
        "id" TEXT PRIMARY KEY,
        "family" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "URItemplate" TEXT,
        "canonicalForm" TEXT NOT NULL,
        "canonicalExample" TEXT NOT NULL,
        "matchExample" TEXT NOT NULL,
        "citationType" TEXT NOT NULL,
        "isCanonical" TEXT NOT NULL,
        "isNeutral" TEXT NOT NULL,
        "jurisdiction" varchar(2) NOT NULL,
        "pattern" TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS "ukpga_lookup" (
        "id" int PRIMARY KEY,
        "ref" TEXT,
        "title" TEXT,
        "ref_version" TEXT,
        "shorttitle" TEXT,
        "citation" TEXT,
        "acronymcitation" TEXT,
        "year" int,
        "candidate_titles" TEXT,
        "for_fuzzy" TEXT
        );"""

        rule_id = "wlr"
        # query_select_data = '''SELECT * FROM manifest WHERE id="{0}"'''.format(rule_id)
        query_select_data = '''SELECT * FROM manifest'''


        # '''SELECT * FROM manifest WHERE id="{0}"'''.format(rule_id), conn
        csr = cxn.cursor()
        csr.execute( query_create_table ) 
        cxn.commit()
        LOGGER.debug('created tables')
        csr.execute( query_select_data )
        cxn.commit()
        len_table = csr.rowcount 
        LOGGER.debug('queried tables')
        
        # random_record = random.randint(1, len_table)
        # query_random_data = f"select names from {table_name} where ix = {random_record};"
        # cxn.execute( query_random_data )

        # record = cxn.fetchall()
        # record = cxn.fetchone()
        rows = csr.fetchall()
        for row in rows:
            LOGGER.debug("id = %s", row[0])

        LOGGER.info( f"{len_table} rows returned sucessfully" ) 

        return {"statusCode" : 200, 
                "body" : f"number of records returned is {len_table}" } 
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        if (cxn!= None):
            if (csr!= None):
                csr.close()
            cxn.close()
            LOGGER.debug("PostgreSQL connection is closed")
