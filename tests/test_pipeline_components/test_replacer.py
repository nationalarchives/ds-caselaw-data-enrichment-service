"""Tests the replacer.replacer module's `write_replacements_file` function"""

import json
import unittest
from collections import namedtuple

from replacer.replacer import write_replacements_file

case = namedtuple("case", "citation_match corrected_citation year URI is_neutral")
abb = namedtuple("abb", "abb_match longform")
leg = namedtuple("leg", "detected_ref href canonical")


CITATION_REPLACEMENTS = [
    case(
        citation_match="[2020] EWHC 537 (Ch)",
        corrected_citation="[2020] EWHC 537 (Ch)",
        year="2020",
        URI="https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537",
        is_neutral=True,
    ),
    case(
        citation_match="[2022] 1 P&CR 123",
        corrected_citation="[2022] 1 P&CR 123",
        year="2022",
        URI="#",
        is_neutral=False,
    ),
]
LEGISLATION_REPLACEMENTS = [
    leg(
        detected_ref="Companies Act 2006",
        href="http://www.legislation.gov.uk/ukpga/2006/46",
        canonical="2006 c. 46",
    ),
    leg(
        detected_ref="Trusts of Land and Appointment of Trustees Act 1996",
        href="https://www.legislation.gov.uk/ukpga/1996/47",
        canonical="1996 c. 47",
    ),
]
ABBREVIATION_REPLACEMENTS = [
    abb(abb_match="Dr Guy", longform="Geoffrey Guy"),
    abb(abb_match="ECTHR", longform="European Court of Human Rights"),
]


class TestWriteReplacementsFile(unittest.TestCase):
    """
    Tests `write_replacements_file` function
    """

    def test_citations(self):
        replacements_string = write_replacements_file(CITATION_REPLACEMENTS)
        replacements = replacements_string.splitlines()
        test_list = [
            "[2020] EWHC 537 (Ch)",
            "[2020] EWHC 537 (Ch)",
            "2020",
            "https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537",
            True,
        ]
        key, value = list(json.loads(replacements[0]).items())[0]
        assert key == "case"
        assert value == test_list
        test_list = ["[2022] 1 P&CR 123", "[2022] 1 P&CR 123", "2022", "#", False]
        key, value = list(json.loads(replacements[1]).items())[0]
        assert key == "case"
        assert value == test_list

    def test_legislation(self):
        replacements_string = write_replacements_file(LEGISLATION_REPLACEMENTS)
        replacements = replacements_string.splitlines()
        test_list = [
            "Companies Act 2006",
            "http://www.legislation.gov.uk/ukpga/2006/46",
            "2006 c. 46",
        ]
        key, value = list(json.loads(replacements[0]).items())[0]
        assert key == "leg"
        assert value == test_list
        test_list = [
            "Trusts of Land and Appointment of Trustees Act 1996",
            "https://www.legislation.gov.uk/ukpga/1996/47",
            "1996 c. 47",
        ]
        key, value = list(json.loads(replacements[1]).items())[0]
        assert key == "leg"
        assert value == test_list

    def test_abbreviations(self):
        replacements_string = write_replacements_file(ABBREVIATION_REPLACEMENTS)
        replacements = replacements_string.splitlines()
        test_list = ["Dr Guy", "Geoffrey Guy"]
        key, value = list(json.loads(replacements[0]).items())[0]
        assert key == "abb"
        assert value == test_list
        test_list = ["ECTHR", "European Court of Human Rights"]
        key, value = list(json.loads(replacements[1]).items())[0]
        assert key == "abb"
        assert value == test_list


if __name__ == "__main__":
    unittest.main()
