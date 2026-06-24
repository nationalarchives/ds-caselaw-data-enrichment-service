import json
import logging

from aws_lambda_powertools.utilities.data_classes import (
    EventBridgeEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

from lambdas.update_legislation_table.database import remove_duplicates
from lambdas.update_legislation_table.fetch_legislation import fetch_legislation
from utils.initialise_db import init_db_engine
from utils.secrets_manager import resolve_secret_value

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

LEGISLATION_TABLE_NAME = "ukpga_lookup"


def _resolve_sparql_credentials() -> tuple[str, str]:
    """Resolve SPARQL username and password from combined secret."""
    secret_json = resolve_secret_value("SPARQL_SECRET_NAME")
    credentials = json.loads(secret_json)
    return credentials["username"], credentials["password"]


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


def update_legislation_table(trigger_date: int | None):
    """
    Updates the legislation database table with data fetched from the
    legislation SPARQL endpoint.

    Parameters
    ----------
    trigger_date : int | None
        An optional integer representing the trigger date for fetching data
    """
    LOGGER.info("Updating the legislation table %s", LEGISLATION_TABLE_NAME)

    sparql_username, sparql_password = _resolve_sparql_credentials()

    engine = init_db_engine()
    LOGGER.info("Engine created")
    legislation_data_frame = fetch_legislation(
        sparql_username,
        sparql_password,
        trigger_date,
    )

    legislation_data_frame.to_sql(LEGISLATION_TABLE_NAME, engine, if_exists="append", index=False)
    with engine.connect() as db_conn:
        remove_duplicates(db_conn, LEGISLATION_TABLE_NAME)
    engine.dispose()

    LOGGER.info("Legislation updated")
