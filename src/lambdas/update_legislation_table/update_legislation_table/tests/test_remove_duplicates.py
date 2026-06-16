import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from ..database import remove_duplicates


@pytest.fixture(scope="function")
def postgres():
    container = PostgresContainer("postgres:17")
    container.start()
    yield container
    container.stop()


def test_remove_duplicates(postgres):
    """
    Given the test table has duplicate rows
    When the function to remove_duplicates is called
    Then the number of rows in the table should be reduced
        due to the removed duplicates
    """
    engine = create_engine(postgres.get_connection_url())
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test_table (name VARCHAR(255), age INTEGER)"))
        conn.execute(text("INSERT INTO test_table (name, age) VALUES ('John', 30), ('John', 30), ('Sarah', 25)"))
        conn.commit()

        remove_duplicates(conn, "test_table")

        result = conn.execute(text("SELECT COUNT(*) FROM test_table")).scalar()
        assert result == 2
