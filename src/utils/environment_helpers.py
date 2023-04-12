"""This module contains functions to read in environment variables"""

import base64
import logging
import os

import boto3

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


def get_database_password():
    aws_secret_name = validate_env_variable("SECRET_PASSWORD_LOOKUP")
    aws_region_name = validate_env_variable("REGION_NAME")
    return _get_aws_secret(aws_secret_name, aws_region_name)


def _get_aws_secret(aws_secret_name, aws_region_name):
    """
    Get aws secret
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
    # added as the validation exception was not being caught
    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
