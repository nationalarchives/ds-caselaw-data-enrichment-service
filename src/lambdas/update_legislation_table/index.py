import logging
from typing import Dict

from lambdas.update_legislation_table.fetch_legislation import (
    fetch_legislation,
)
from utils.environment_helpers import validate_env_variable
from utils.initialise_db import init_db_engine

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

LEGISLATION_TABLE_NAME = "ukpga_lookup"


def handler(event: Dict, context) -> None:
    """
    Function called by the lambda to update the legislation table
    """
    LOGGER.info("Updating the legislation table %s", LEGISLATION_TABLE_NAME)

    sparql_username = validate_env_variable("SPARQL_USERNAME")
    sparql_password = validate_env_variable("SPARQL_PASSWORD")

    trigger_date = event.get("trigger_date")
    if not isinstance(trigger_date, int):
        trigger_date = None

    legislation_data_frame = fetch_legislation(
        sparql_username, sparql_password, trigger_date
    )

    engine = init_db_engine()
    LOGGER.info("Engine created")
    legislation_data_frame.to_sql(
        LEGISLATION_TABLE_NAME, engine, if_exists="append", index=False
    )
    engine.dispose()

    LOGGER.info("Legislation updated")
