"""Unit tests for environment_helpers"""

import boto3
import pytest
from moto import mock_secretsmanager

from utils.environment_helpers import (
    get_database_password,
    validate_env_variable,
)


class TestValidateEnvVariable:
    def test_validate_env_variable_success(self, monkeypatch):
        """
        Given an environment variable name
        When the environment variable has a value
        Then validate_env_variable should return the value of the environment variable
        """
        env_var_name = "DATABASE_PASSWORD"
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
        with pytest.raises(Exception):
            validate_env_variable(env_var_name)

    def test_validate_env_variable_failure(self):
        """
        Given an environment variable name
        When the environment variable does not exist
        Then validate_env_variable should raise an Exception
        """
        env_var_name = "NON_EXISTENT_VAR"
        with pytest.raises(Exception):
            validate_env_variable(env_var_name)


class TestGetDatabasePassword:
    @pytest.fixture(scope="class", autouse=True)
    def setup_moto_secrets_manager(self):
        secret_value = {"SecretString": "mydatabasepassword"}
        region_name = "us-east-1"
        secret_name = "mysecret"
        mock_secrets_manager = mock_secretsmanager()
        mock_secrets_manager.start()
        client = boto3.client("secretsmanager", region_name=region_name)
        client.create_secret(
            Name=secret_name, SecretString=secret_value["SecretString"]
        )
        yield {
            "secret_value": secret_value,
            "region_name": region_name,
            "secret_name": secret_name,
        }

    def test_get_database_password_with_database_password(self, monkeypatch):
        """
        Given the DATABASE_PASSWORD environment variable is set
        When get_database_password is called
        Then get_database_password should return the value of the DATABASE_PASSWORD environment variable
        """
        monkeypatch.setenv("DATABASE_PASSWORD", "my_database_password")
        monkeypatch.setenv("SECRET_PASSWORD_LOOKUP", "my_secret_name")
        monkeypatch.setenv("REGION_NAME", "us-west-2")

        assert get_database_password() == "my_database_password"

    def test_get_database_password_with_valid_aws_secret(
        self, monkeypatch, setup_moto_secrets_manager
    ):
        """
        Given a valid AWS secret containing the database password
        When I call get_database_password
        Then I should get the correct database password
        """
        monkeypatch.setenv(
            "SECRET_PASSWORD_LOOKUP", setup_moto_secrets_manager["secret_name"]
        )
        monkeypatch.setenv("REGION_NAME", setup_moto_secrets_manager["region_name"])

        password = get_database_password()

        assert password == setup_moto_secrets_manager["secret_value"]["SecretString"]

    def test_get_database_password_with_no_env_variables(self):
        """
        Given no DATABASE_PASSWORD, SECRET_PASSWORD_LOOKUP or REGION_NAME
        environment variables are set
        When get_database_password is called
        Then get_database_password should raise an Exception
        """
        with pytest.raises(Exception):
            get_database_password()

    def test_get_database_password_with_invalid_aws_secret_password_lookup(
        self, monkeypatch, setup_moto_secrets_manager
    ):
        """
        Given an invalid AWS secret name
        When I call get_database_password
        Then I should get an exception
        """
        monkeypatch.setenv("SECRET_PASSWORD_LOOKUP", "wrong_password")
        monkeypatch.setenv("REGION_NAME", setup_moto_secrets_manager["region_name"])

        with pytest.raises(Exception):
            get_database_password()

    def test_get_database_password_with_invalid_aws_region(
        self, monkeypatch, setup_moto_secrets_manager
    ):
        """
        Given an invalid AWS region
        When I call get_database_password
        Then I should get an exception
        """
        monkeypatch.setenv(
            "SECRET_PASSWORD_LOOKUP", setup_moto_secrets_manager["secret_name"]
        )
        monkeypatch.setenv("REGION_NAME", "wrong-region")

        with pytest.raises(Exception):
            get_database_password()
