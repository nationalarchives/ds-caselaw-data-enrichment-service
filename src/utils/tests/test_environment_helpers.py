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
    def test_get_database_password_with_valid_aws_secret(
        self, monkeypatch, moto_secrets_manager_with_password
    ):
        """
        Given a valid AWS secret containing the database password
        When I call get_database_password
        Then I should get the correct database password
        """
        monkeypatch.setenv(
            "SECRET_PASSWORD_LOOKUP", moto_secrets_manager_with_password["secret_name"]
        )
        monkeypatch.setenv(
            "REGION_NAME", moto_secrets_manager_with_password["region_name"]
        )

        password = get_database_password()

        assert (
            password
            == moto_secrets_manager_with_password["secret_value"]["SecretString"]
        )

    def test_get_database_password_with_no_env_variables(self):
        """
        Given no SECRET_PASSWORD_LOOKUP or REGION_NAME
        environment variables are set
        When get_database_password is called
        Then get_database_password should raise an Exception
        """
        with pytest.raises(Exception):
            get_database_password()

    def test_get_database_password_with_invalid_aws_secret_password_lookup(
        self, monkeypatch, moto_secrets_manager_with_password
    ):
        """
        Given an invalid AWS secret name
        When I call get_database_password
        Then I should get an exception
        """
        monkeypatch.setenv("SECRET_PASSWORD_LOOKUP", "wrong_password")
        monkeypatch.setenv(
            "REGION_NAME", moto_secrets_manager_with_password["region_name"]
        )

        with pytest.raises(Exception):
            get_database_password()

    def test_get_database_password_with_invalid_aws_region(
        self, monkeypatch, moto_secrets_manager_with_password
    ):
        """
        Given an invalid AWS region
        When I call get_database_password
        Then I should get an exception
        """
        monkeypatch.setenv(
            "SECRET_PASSWORD_LOOKUP", moto_secrets_manager_with_password["secret_name"]
        )
        monkeypatch.setenv("REGION_NAME", "wrong-region")

        with pytest.raises(Exception):
            get_database_password()
