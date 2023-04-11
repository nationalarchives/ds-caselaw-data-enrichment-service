"""
This module contains functions to initialise db connections
from environment variables
"""

import psycopg2
import sqlalchemy

from database.db_connection import create_connection
from utils.environment_helpers import (
    get_database_password,
    validate_env_variable,
)

DATABASE_NAME = validate_env_variable("DATABASE_NAME")
USERNAME = validate_env_variable("DATABASE_USERNAME")
HOST = validate_env_variable("DATABASE_HOSTNAME")
PORT = validate_env_variable("DATABASE_PORT")
PASSWORD = get_database_password()


def init_db_engine() -> sqlalchemy.Engine:
    db_url = "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        USERNAME, PASSWORD, HOST, PORT, DATABASE_NAME
    )
    return sqlalchemy.create_engine(db_url, verbose=True)


def init_db_connection() -> psycopg2.connection:
    """
    Establish database connection
    """
    return create_connection(
        DATABASE_NAME,
        USERNAME,
        PASSWORD,
        HOST,
        PORT,
    )
