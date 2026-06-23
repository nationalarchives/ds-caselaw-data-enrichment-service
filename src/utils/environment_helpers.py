"""This module contains functions to read in environment variables"""

import logging
import os

import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class MissingEnvironmentVariableError(Exception):
    pass


def validate_env_variable(env_var_name: str) -> str:
    print(f"Getting the value of the environment variable: {env_var_name}")

    try:
        env_variable = os.environ[env_var_name]
    except KeyError as err:
        msg = f"Please, set environment variable {env_var_name}"
        raise MissingEnvironmentVariableError(msg) from err

    if not env_variable:
        msg = f"Please, provide environment variable {env_var_name}"
        raise MissingEnvironmentVariableError(msg)

    return env_variable


def get_aws_secret(aws_secret_name: str) -> str:
    """
    Get aws secret value from AWS Secrets Manager using boto3 client
    """
    if not aws_secret_name:
        msg = "No aws_secret_name provided"
        raise RuntimeError(msg)

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        LOGGER.info(" about to get_secret_value_response")
        get_secret_value_response = client.get_secret_value(SecretId=aws_secret_name)
    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise
    LOGGER.info("got_secret_value_response")
    return get_secret_value_response["SecretString"]
