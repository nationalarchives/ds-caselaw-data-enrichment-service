"""
This module contains functions to initialise db connections
from environment variables
"""

import psycopg2
import sqlalchemy

from database.db_connection import create_connection
from utils.environment_helpers import get_aws_secret, validate_env_variable


def init_db_engine() -> sqlalchemy.Engine:
    """
    Initialise database engine from environment variables
    """
    database_name = validate_env_variable("DATABASE_NAME")
    username = validate_env_variable("DATABASE_USERNAME")
    host = validate_env_variable("DATABASE_HOSTNAME")
    port = validate_env_variable("DATABASE_PORT")
    password = _get_database_password()

    db_url = "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        username, password, host, port, database_name
    )
    return sqlalchemy.create_engine(db_url)


def init_db_connection() -> psycopg2.extensions.connection:
    """
    Initialise database connection from environment variables
    """
    database_name = validate_env_variable("DATABASE_NAME")
    username = validate_env_variable("DATABASE_USERNAME")
    host = validate_env_variable("DATABASE_HOSTNAME")
    port = validate_env_variable("DATABASE_PORT")
    password = _get_database_password()

    return create_connection(
        database_name,
        username,
        password,
        host,
        port,
    )


def _get_database_password():
    aws_secret_name = validate_env_variable("SECRET_PASSWORD_LOOKUP")
    aws_region_name = validate_env_variable("REGION_NAME")
    return get_aws_secret(aws_secret_name, aws_region_name)
