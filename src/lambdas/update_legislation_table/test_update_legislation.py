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
    sql_query = """
    CREATE TABLE ukpga_lookup (
        ref VARCHAR(100) NOT NULL,
        title VARCHAR(100) NOT NULL,
        ref_version VARCHAR(100) NOT NULL,
        shorttitle VARCHAR(100) NOT NULL,
        citation VARCHAR(100) NOT NULL,
        acronymcitation VARCHAR(100) NOT NULL,
        year BIGINT NOT NULL,
        candidate_titles VARCHAR(100) NOT NULL,
        for_fuzzy BOOLEAN NOT NULL
    );
    INSERT INTO ukpga_lookup (ref, title, ref_version, shorttitle, citation, acronymcitation, year, candidate_titles, for_fuzzy)
    VALUES
        ('a', 'a_title', 'a_ref_version', 'a_shorttitle', 'a_citation', 'a_acronymcitation', 2001, 'a_candidate_titles', true),
        ('b', 'b_title', 'b_ref_version', 'b_shorttitle', 'b_citation', 'b_acronymcitation', 2001, 'b_candidate_titles', true)
    """
    conn.cursor().execute(sql_query)
    yield conn
    conn.cursor().execute("DROP TABLE ukpga_lookup")


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

    mock_fetch_legislation.return_value = pd.DataFrame(
        {
            "ref": ["b", "c"],
            "title": ["b_title", "c_title"],
            "ref_version": ["b_ref_version", "c_ref_version"],
            "shorttitle": ["b_shorttitle", "c_shorttitle"],
            "citation": ["b_citation", "c_citation"],
            "acronymcitation": ["b_acronymcitation", "c_acronymcitation"],
            "year": [2001, 2001],
            "candidate_titles": ["b_candidate_titles", "c_candidate_titles"],
            "for_fuzzy": [True, True],
        }
    )

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
    assert rows == [
        (
            "a",
            "a_title",
            "a_ref_version",
            "a_shorttitle",
            "a_citation",
            "a_acronymcitation",
            2001,
            "a_candidate_titles",
            True,
        ),
        (
            "b",
            "b_title",
            "b_ref_version",
            "b_shorttitle",
            "b_citation",
            "b_acronymcitation",
            2001,
            "b_candidate_titles",
            True,
        ),
        (
            "c",
            "c_title",
            "c_ref_version",
            "c_shorttitle",
            "c_citation",
            "c_acronymcitation",
            2001,
            "c_candidate_titles",
            True,
        ),
    ]
