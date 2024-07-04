import logging
from typing import Optional

from aws_lambda_powertools.utilities.data_classes import (
    EventBridgeEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from update_legislation_table.database import remove_duplicates
from update_legislation_table.fetch_legislation import fetch_legislation

from utils.environment_helpers import validate_env_variable
from utils.initialise_db import init_db_engine

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

LEGISLATION_TABLE_NAME = "ukpga_lookup"


@event_source(data_class=EventBridgeEvent)
def handler(event: EventBridgeEvent, context: LambdaContext) -> None:
    """
    Lambda function handler that updates the legislation table
    """
    try:
        trigger_date = event.get("trigger_date")
        if not isinstance(trigger_date, int):
            trigger_date = None
        update_legislation_table(trigger_date)
    except Exception as exception:
        LOGGER.error("Exception: %s", exception)
        raise


def update_legislation_table(trigger_date: Optional[int]):
    """
    Updates the legislation database table with data fetched from the
    legislation SPARQL endpoint.

    Parameters
    ----------
    trigger_date int optional
        An optional integer representing the trigger date for fetching data
    """
    LOGGER.info("Updating the legislation table %s", LEGISLATION_TABLE_NAME)

    sparql_username = validate_env_variable("SPARQL_USERNAME")
    sparql_password = validate_env_variable("SPARQL_PASSWORD")

    legislation_data_frame = fetch_legislation(sparql_username, sparql_password, trigger_date)

    engine = init_db_engine()
    LOGGER.info("Engine created")
    legislation_data_frame.to_sql(LEGISLATION_TABLE_NAME, engine, if_exists="append", index=False)
    with engine.connect() as db_conn:
        remove_duplicates(db_conn, LEGISLATION_TABLE_NAME)
    engine.dispose()

    LOGGER.info("Legislation updated")
