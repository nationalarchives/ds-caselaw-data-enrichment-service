"""Fixtures for utils tests"""

import boto3
import pytest
from moto import mock_aws


@pytest.fixture()
def moto_secrets_manager_with_password():
    secret_value = {"SecretString": "mydatabasepassword"}
    region_name = "us-east-1"
    secret_name = "mysecret"  # noqa: S105
    mock_secrets_manager = mock_aws()
    mock_secrets_manager.start()

    client = boto3.client("secretsmanager", region_name=region_name)
    client.create_secret(Name=secret_name, SecretString=secret_value["SecretString"])

    yield {
        "secret_value": secret_value,
        "region_name": region_name,
        "secret_name": secret_name,
    }

    mock_secrets_manager.stop()
