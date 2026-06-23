"""Unit tests for environment_helpers"""

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from utils.environment_helpers import MissingEnvironmentVariableError, get_aws_secret, validate_env_variable


class TestValidateEnvVariable:
    def test_validate_env_variable_success(self, monkeypatch):
        """
        Given an environment variable name
        When the environment variable has a value
        Then validate_env_variable should return the value of the environment variable
        """
        env_var_name = "MY_ENV_VAR"
        monkeypatch.setenv(env_var_name, "my_password")
        result = validate_env_variable(env_var_name)
        assert result == "my_password"

    def test_validate_env_variable_empty(self, monkeypatch):
        """
        Given an environment variable name
        When the environment variable has an empty string as its value
        Then validate_env_variable should raise an Exception
        """
        env_var_name = "EMPTY_VAR"
        monkeypatch.setenv(env_var_name, "")
        with pytest.raises(MissingEnvironmentVariableError):
            validate_env_variable(env_var_name)

    def test_validate_env_variable_failure(self):
        """
        Given an environment variable name
        When the environment variable does not exist
        Then validate_env_variable should raise an Exception
        """
        env_var_name = "NON_EXISTENT_VAR"
        with pytest.raises(MissingEnvironmentVariableError):
            validate_env_variable(env_var_name)


class TestGetAWSSecret:
    @mock_aws
    def test_get_aws_secret_with_valid_aws_secret(self, monkeypatch):
        """
        Given a valid AWS secret containing the database password
        When I call get_aws_secret
        Then I should get the correct database password
        """
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        secret_name = "test_secret_name"  # noqa: S105
        secret_value = "test_secret_value"  # noqa: S105
        client = boto3.client("secretsmanager")
        client.create_secret(Name=secret_name, SecretString=secret_value)

        password = get_aws_secret(secret_name)

        assert password == secret_value

    @mock_aws
    def test_get_aws_secret_with_empty_secret_name(self, monkeypatch):
        """
        Given aws_secret_name is empty
        When get_aws_secret is called with it
        Then get_aws_secret should raise an Exception
        """
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        secret_name = "test_secret_name"  # noqa: S105
        secret_value = "test_secret_value"  # noqa: S105
        client = boto3.client("secretsmanager")
        client.create_secret(Name=secret_name, SecretString=secret_value)
        with pytest.raises(RuntimeError):
            get_aws_secret("")

    @mock_aws
    def test_get_aws_secret_with_invalid_aws_secret_password_lookup(self, monkeypatch):
        """
        Given an invalid AWS secret name
        When I call get_aws_secret
        Then get_aws_secret should raise an Exception
        """
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        secret_name = "test_secret_name"  # noqa: S105
        secret_value = "test_secret_value"  # noqa: S105
        client = boto3.client("secretsmanager")
        client.create_secret(Name=secret_name, SecretString=secret_value)
        with pytest.raises(ClientError):
            get_aws_secret("wrong_password")

    @mock_aws
    def test_get_aws_secret_with_invalid_aws_region(self, monkeypatch):
        """
        Given an invalid AWS region
        When I call get_aws_secret
        Then get_aws_secret should raise a KeyError
        """
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        secret_name = "test_secret_name"  # noqa: S105
        secret_value = "test_secret_value"  # noqa: S105
        client = boto3.client("secretsmanager")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "invalid-region")
        client.create_secret(Name=secret_name, SecretString=secret_value)
        with pytest.raises(KeyError):
            get_aws_secret(secret_name)
