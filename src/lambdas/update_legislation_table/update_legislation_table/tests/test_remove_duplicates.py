from sqlalchemy import text

from ..database import remove_duplicates


def test_remove_duplicates(db_connection):
    """
    Given the test table has duplicate rows
    When the function to remove_duplicates is called
    Then the number of rows in the table should be reduced
        due to the removed duplicates
    """
    db_connection.execute(text("CREATE TABLE test_table (name VARCHAR(255), age INTEGER)"))
    db_connection.execute(text("INSERT INTO test_table (name, age) VALUES ('John', 30), ('John', 30), ('Sarah', 25)"))
    db_connection.commit()

    remove_duplicates(db_connection, "test_table")

    result = db_connection.execute(text("SELECT COUNT(*) FROM test_table")).scalar()
    assert result == 2
