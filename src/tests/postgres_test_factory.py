import os
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse
from uuid import uuid4

import psycopg2

if TYPE_CHECKING:
    from unittest import TestCase


INVALID_TEST_POSTGRES_URL_MSG = "TEST_POSTGRES_URL must start with postgres:// or postgresql://"
MISSING_DB_NAME_MSG = "TEST_POSTGRES_URL must include a database name"
MISSING_TEST_POSTGRES_URL_MSG = (
    "TEST_POSTGRES_URL is required for DB-backed tests. Run tests via make test to provision PostgreSQL automatically."
)


@dataclass
class ExternalPostgresql:
    _url: str
    _database_name: str | None = None

    def dsn(self) -> dict:
        parsed = urlparse(self._url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError(INVALID_TEST_POSTGRES_URL_MSG)
        database = self._database_name or parsed.path.lstrip("/")
        if not database:
            raise ValueError(MISSING_DB_NAME_MSG)
        return {
            "host": parsed.hostname or "127.0.0.1",
            "port": parsed.port or 5432,
            "user": unquote(parsed.username or "postgres"),
            "password": unquote(parsed.password or ""),
            "database": database,
        }

    def url(self) -> str:
        parsed = urlparse(self._url)
        if not self._database_name:
            return self._url
        base = f"{parsed.scheme}://"
        if parsed.username:
            base += unquote(parsed.username)
            if parsed.password:
                base += f":{unquote(parsed.password)}"
            base += "@"
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5432
        return f"{base}{host}:{port}/{self._database_name}"

    def __enter__(self):
        parsed = urlparse(self._url)
        base_database = parsed.path.lstrip("/")
        if not base_database:
            raise ValueError(MISSING_DB_NAME_MSG)

        self._database_name = f"test_{uuid4().hex}"
        admin_conn = psycopg2.connect(**self._admin_dsn(base_database))
        admin_conn.autocommit = True
        try:
            with admin_conn.cursor() as cursor:
                cursor.execute(f'CREATE DATABASE "{self._database_name}"')
        finally:
            admin_conn.close()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._database_name:
            return

        parsed = urlparse(self._url)
        base_database = parsed.path.lstrip("/")
        admin_conn = psycopg2.connect(**self._admin_dsn(base_database))
        admin_conn.autocommit = True
        try:
            with admin_conn.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                    (self._database_name,),
                )
                cursor.execute(f'DROP DATABASE IF EXISTS "{self._database_name}"')
        finally:
            admin_conn.close()

    def _admin_dsn(self, database: str) -> dict:
        parsed = urlparse(self._url)
        return {
            "host": parsed.hostname or "127.0.0.1",
            "port": parsed.port or 5432,
            "user": unquote(parsed.username or "postgres"),
            "password": unquote(parsed.password or ""),
            "database": database,
        }


@contextmanager
def postgres_instance():
    external_url = os.getenv("TEST_POSTGRES_URL")
    if not external_url:
        raise RuntimeError(MISSING_TEST_POSTGRES_URL_MSG)

    with ExternalPostgresql(external_url) as postgresql:
        yield postgresql


def postgres_for_unittest(test_case: "TestCase"):
    """Create a postgres instance and register cleanup on a unittest.TestCase."""
    stack = ExitStack()
    test_case.addCleanup(stack.close)
    return stack.enter_context(postgres_instance())
