"""
Integration test file for fetch_legislation module.

Note that these tests require valid credentials for the SPARQL endpoint.
The credentials should be stored in environment variables named
'SPARQL_USERNAME' and 'SPARQL_PASSWORD'.
"""

import datetime
import os
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from dotenv import load_dotenv

from ..fetch_legislation import fetch_legislation

# Do not truncate debug output
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)


@pytest.fixture(scope="module")
def set_env_vars():
    load_dotenv()
    yield
    del os.environ["SPARQL_USERNAME"]
    del os.environ["SPARQL_PASSWORD"]


frozen_now_time = datetime.datetime(2023, 4, 13, 3, tzinfo=datetime.UTC)


@pytest.mark.integration
@patch("update_legislation_table.fetch_legislation.datetime.datetime")
def test_fetch_legislation_integration(mock_datetime, set_env_vars) -> None:
    """
    GIVEN a set of environment variables including SPARQL_USERNAME and SPARQL_PASSWORD
    WHEN fetch_legislation is called with a mocked date
    THEN the resulting DataFrame should be as expected
    """
    # GIVEN
    mock_datetime.now.return_value = frozen_now_time

    # WHEN
    sparql_username = os.environ.get("SPARQL_USERNAME", "")
    sparql_password = os.environ.get("SPARQL_PASSWORD", "")

    days = 16

    result = fetch_legislation(sparql_username, sparql_password, days)

    # THEN
    expected_df = pd.DataFrame(
        {
            "ref": [
                "http://www.legislation.gov.uk/id/ukpga/2023/10",
                "http://www.legislation.gov.uk/id/ukpga/2023/10",
                "http://www.legislation.gov.uk/id/ukpga/2023/8",
                "http://www.legislation.gov.uk/id/ukpga/2023/8",
            ],
            "title": [
                "UK Infrastructure Bank Act 2023",
                "UK Infrastructure Bank Act 2023",
                "Seafarers Wages Act 2023",
                "Seafarers Wages Act 2023",
            ],
            "ref_version": [
                "http://www.legislation.gov.uk/ukpga/2023/10",
                "http://www.legislation.gov.uk/ukpga/2023/10",
                "http://www.legislation.gov.uk/ukpga/2023/8/enacted",
                "http://www.legislation.gov.uk/ukpga/2023/8/enacted",
            ],
            "shorttitle": [
                "UK Infrastructure Bank Act 2023",
                "UK Infrastructure Bank Act 2023",
                "Seafarers Wages Act 2023",
                "Seafarers Wages Act 2023",
            ],
            "citation": ["2023 c. 10", "2023 c. 10", "2023 c. 8", "2023 c. 8"],
            "acronymcitation": [np.nan, np.nan, np.nan, np.nan],
            "year": [2023, 2023, 2023, 2023],
            "candidate_titles": [
                "UK Infrastructure Bank Act 2023",
                "2023 c. 10",
                "Seafarers Wages Act 2023",
                "2023 c. 8",
            ],
            "for_fuzzy": [True, False, True, False],
        },
        index=[0, 0, 2, 2],
    )
    assert result.equals(expected_df)
