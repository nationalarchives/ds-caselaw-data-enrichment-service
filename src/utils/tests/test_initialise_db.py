"""Unit tests for the initialise_db module"""
from unittest import mock

from mock import MagicMock

from utils.initialise_db import init_db_connection, init_db_engine


@mock.patch("sqlalchemy.create_engine")
def test_init_db_engine(mock_create_engine, monkeypatch):
    """
    Given: The environment variables for the database are set
    When: The `init_db_engine` function is called
    Then create_engine was called with the correct arguments
    """
    monkeypatch.setenv("DATABASE_NAME", "mydb")
    monkeypatch.setenv("DATABASE_USERNAME", "myuser")
    monkeypatch.setenv("DATABASE_HOSTNAME", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_PASSWORD", "mypass")

    mock_create_engine.return_value = MagicMock()

    engine = init_db_engine()

    expected_db_url = "postgresql://myuser:mypass@localhost:5432/mydb"
    mock_create_engine.assert_called_once_with(expected_db_url, verbose=True)
    assert engine == mock_create_engine.return_value


@mock.patch("utils.initialise_db.create_connection")
def test_init_db_connection(mock_create_engine, monkeypatch):
    """
    Given: The environment variables for the database are set
    When: The `init_db_connection` function is called
    Then create_connection was called with the correct arguments
    """
    monkeypatch.setenv("DATABASE_NAME", "mydb")
    monkeypatch.setenv("DATABASE_USERNAME", "myuser")
    monkeypatch.setenv("DATABASE_HOSTNAME", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_PASSWORD", "mypass")

    mock_create_engine.return_value = MagicMock()

    engine = init_db_connection()

    mock_create_engine.assert_called_once_with(
        "mydb", "myuser", "mypass", "localhost", "5432"
    )
    assert engine == mock_create_engine.return_value
