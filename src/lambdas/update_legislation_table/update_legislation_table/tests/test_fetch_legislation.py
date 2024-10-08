from unittest.mock import patch

import numpy as np
import pandas as pd

from ..fetch_legislation import fetch_legislation

# Do not truncate debug output
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)


@patch("update_legislation_table.fetch_legislation.SPARQLWrapper")
def test_fetch_legislation_canned(mock_sparql_wrapper) -> None:
    # GIVEN
    canned_sparql_response = b'"ref","title","ref_version","shorttitle","citation","acronymcitation","year"\n"http://www.legislation.gov.uk/id/ukpga/2023/10","UK Infrastructure Bank Act 2023","http://www.legislation.gov.uk/ukpga/2023/10","UK Infrastructure Bank Act 2023","2023 c. 10",,2023\n"http://www.legislation.gov.uk/id/ukpga/2023/10","UK Infrastructure Bank Act 2023","http://www.legislation.gov.uk/ukpga/2023/10/enacted","UK Infrastructure Bank Act 2023","2023 c. 10",,2023\n"http://www.legislation.gov.uk/id/ukpga/2023/8","Seafarers Wages Act 2023","http://www.legislation.gov.uk/ukpga/2023/8/enacted","Seafarers Wages Act 2023","2023 c. 8",,2023\n"http://www.legislation.gov.uk/id/ukpga/2023/8","Seafarers Wages Act 2023","http://www.legislation.gov.uk/ukpga/2023/8","Seafarers Wages Act 2023","2023 c. 8",,2023\n'
    mock_sparql_wrapper.return_value.query.return_value.convert.return_value = canned_sparql_response

    # WHEN
    sparql_username = "tess_testerton"
    sparql_password = "hunter2"  # noqa: S105

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
