from unittest.mock import patch

import boto3
import pandas as pd
import pytest
from index import update_legislation_table
from moto import mock_secretsmanager
from pytest_postgresql import factories

postgresql_my_proc = factories.postgresql_proc(
    user="testuser",
    host="localhost",
    port=5431,
    dbname="testdb",
    password="secret_password",
)
postgresql_my = factories.postgresql("postgresql_my_proc")


@pytest.fixture
def test_db_connection(postgresql_my):
    conn = postgresql_my
    conn.autocommit = True
    conn.cursor().execute("CREATE DATABASE ukpga_lookup")
    yield conn
    conn.cursor().execute("DROP DATABASE ukpga_lookup")


@pytest.fixture(scope="function")
def setup_moto_secrets_manager():
    secret_value = {"SecretString": "secret_password"}
    region_name = "us-east-1"
    secret_name = "mysecret"
    mock_secrets_manager = mock_secretsmanager()
    mock_secrets_manager.start()
    client = boto3.client("secretsmanager", region_name=region_name)
    client.create_secret(Name=secret_name, SecretString=secret_value["SecretString"])
    yield {
        "secret_value": secret_value,
        "region_name": region_name,
        "secret_name": secret_name,
    }


@patch("index.fetch_legislation")
def test_update_legislation_table(
    mock_fetch_legislation,
    monkeypatch,
    setup_moto_secrets_manager,
    test_db_connection,
):
    """
    Given a postgres database and valid environment variables matching this database
    When update_legislation_table is called with a trigger_date
    Then the ukpga_lookup table in the database is appended to with the legislation
        entries from fetch_legislation
    """
    mock_fetch_legislation.return_value = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})

    monkeypatch.setenv("SPARQL_USERNAME", "test_user")
    monkeypatch.setenv("SPARQL_PASSWORD", "test_password")
    monkeypatch.setenv("DATABASE_NAME", "testdb")
    monkeypatch.setenv("DATABASE_USERNAME", "testuser")
    monkeypatch.setenv("DATABASE_HOSTNAME", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5431")
    monkeypatch.setenv(
        "SECRET_PASSWORD_LOOKUP", setup_moto_secrets_manager["secret_name"]
    )
    monkeypatch.setenv("REGION_NAME", setup_moto_secrets_manager["region_name"])

    trigger_date = 7
    update_legislation_table(trigger_date)
    mock_fetch_legislation.assert_called_with("test_user", "test_password", 7)
    rows = test_db_connection.cursor().execute("SELECT * FROM ukpga_lookup").fetchall()
    assert len(rows) == 2
    assert rows == [(1, 2), (3, 4)]
