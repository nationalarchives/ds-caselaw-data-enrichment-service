"""
This module contains utility functions for working with databases using SQLAlchemy.
"""

from sqlalchemy import Connection, text


def remove_duplicates(db_conn: Connection, table_name: str) -> None:
    """
    Removes duplicate rows from the specified table in the database.
    Uses a SQL query to identify duplicate rows based on all columns, except for the
    unique row identifier, and deletes all but one of the duplicate rows.
    Parameters
    ----------
    db_conn: sqlalchemy.engine.Connection, required.
        The SQLAlchemy database connection object.
    table_name: str, required.
        The name of the table to remove duplicates from.
    Returns
    -------
    None
    """
    sql_string = f"""
        DELETE FROM {table_name}
        WHERE ctid IN (
        SELECT ctid
        FROM (
            SELECT ctid, ROW_NUMBER() OVER(PARTITION BY {table_name}.*) AS rnum
            FROM {table_name}
        ) t
        WHERE t.rnum > 1
        );
    """
    db_conn.execute(text(sql_string))
    db_conn.commit()
