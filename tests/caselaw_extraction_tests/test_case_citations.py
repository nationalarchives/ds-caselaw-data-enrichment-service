"""
    Testing the matching of the citations based on the data found in the rules.
    These are independent unit tests.
"""

import sys
import unittest

import pandas as pd
import psycopg2
import testing.postgresql
from spacy.lang.en import English
from sqlalchemy import create_engine

sys.path.append("./")

from caselaw_extraction.correction_strategies import apply_correction_strategy
from database.db_connection import get_matched_rule
from replacer.replacer import replacer_caselaw
from utils.helper import load_patterns


CORRECT_CITATIONS = [
    "random text goes here random text goes here **[2022] UKUT 177 (TCC)",
    "[2022] 1 Lloyd's Rep 123.",
    "..........Case C-123/12........",
    "[[2022] EWHC 123 (Mercantile) ",
    "[2022] EWHC 123 (TCC))",
    "random text goes here [2022] 1 WLR 123 random text goes here",
    "random text goes here random text goes here [2022] UKUT 123 (TCC)",
    "random text [2004] AC 816 goes here  random text goes here "
    "[2022] EWHC 123 (Pat)",
    "......[2022] 1 QB 123......",
]
INCORRECT_CITATIONS = [
    "random text goes here (2022) UKUT 123 (IAC) random text goes here",
    "[2057] A.C. 657 random text goes here",
]
UNKNOWN_CITATIONS = [
    "random text goes here random text goes here [2022] UKUT 177  (TCC)",
    "gCase C-123/12",
    "[2022]] UKUT 177 (TCC)",
]


# create mock function for the db connection - extracting the logic from main.py
def mock_return_citation(nlp, text, db_conn):
    doc = nlp(text)
    citation_match = None
    is_canonical = None
    citation_type = None
    canonical_form = None
    family = None
    URItemplate = None
    is_neutral = None
    for ent in doc.ents:
        rule_id = ent.ent_id_
        citation_match = ent.text
        # TODO: this should be mocked
        (
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = get_matched_rule(db_conn, rule_id)
    return (
        citation_match,
        family,
        URItemplate,
        is_neutral,
        is_canonical,
        citation_type,
        canonical_form,
    )


# current number of rules in the database
def mock_get_rules_total(db_conn):
    cursor = db_conn.cursor()
    number_of_rules = cursor.execute("""SELECT COUNT(*) FROM manifest""")

    return number_of_rules


class TestCitationProcessor(unittest.TestCase):
    """
    This class focuses on testing the Citation Processor, which gathers the results from the DB. This class primarily uses the mock_return_citation method.
    This includes testing incorrect or missing citations.
    This is relevant for the logic performed in main.py
    """

    def setUp(self):
        self.nlp = English()
        self.nlp.max_length = 1500000
        self.nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

        self.postgresql = testing.postgresql.Postgresql()
        self.db_conn = psycopg2.connect(**self.postgresql.dsn())
        engine = create_engine(self.postgresql.url())

        manifest_df = pd.read_csv("rules/2022_04_08_Citation_Manifest.csv")
        manifest_df.to_sql("manifest", engine, if_exists="append", index=False)

    def tearDown(self):
        self.postgresql.stop()

    # Handling extra characters around the citations to ensure that spacy handles it well
    def test_citation_matching(self):
        # including additional text around the citation to handling the parsing
        text = "!!!!!!!_________[2047] Costs LR 123_____"
        (
            citation_match,
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical == True

        text = "[2022] UKFTT 2020__0341 (GRC)"
        (
            citation_match,
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical is None

        text = "amy [2022] KB 123"
        (
            citation_match,
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical == True

    # for correct citations - ensure it finds that it is canonical
    def test_correct_canonical(self):
        for text in CORRECT_CITATIONS:
            (
                citation_match,
                family,
                URItemplate,
                is_neutral,
                is_canonical,
                citation_type,
                canonical_form,
            ) = mock_return_citation(self.nlp, text, self.db_conn)
            print("Testing: " + text)
            assert is_canonical == True

    # for correct citations - make sure it finds the citation type & the citation in the DB
    def test_citation_type_found(self):
        for text in CORRECT_CITATIONS:
            (
                citation_match,
                family,
                URItemplate,
                is_neutral,
                is_canonical,
                citation_type,
                canonical_form,
            ) = mock_return_citation(self.nlp, text, self.db_conn)
            print("Testing: " + text)
            assert citation_type is not None

    # for correct citations - make sure it finds the canonical form (if its not found, it will be None)
    def test_canonical_form_found(self):
        for text in CORRECT_CITATIONS:
            (
                citation_match,
                family,
                URItemplate,
                is_neutral,
                is_canonical,
                citation_type,
                canonical_form,
            ) = mock_return_citation(self.nlp, text, self.db_conn)
            print("Testing: " + text)
            assert canonical_form is not None

    def test_incorrect_canonical_form(self):
        for text in INCORRECT_CITATIONS:
            (
                citation_match,
                family,
                URItemplate,
                is_neutral,
                is_canonical,
                citation_type,
                canonical_form,
            ) = mock_return_citation(self.nlp, text, self.db_conn)
            print("Testing: " + text)
            assert is_canonical == False
            assert type(canonical_form) is str

    def test_incorrect_citation_match(self):
        for text in INCORRECT_CITATIONS:
            (
                citation_match,
                family,
                URItemplate,
                is_neutral,
                is_canonical,
                citation_type,
                canonical_form,
            ) = mock_return_citation(self.nlp, text, self.db_conn)
            print("Testing: " + text)
            assert citation_match is not None

    def test_unknown_citations(self):
        for text in UNKNOWN_CITATIONS:
            print("Testing: " + text)
            (
                citation_match,
                family,
                URItemplate,
                is_neutral,
                is_canonical,
                citation_type,
                canonical_form,
            ) = mock_return_citation(self.nlp, text, self.db_conn)
            assert is_canonical != True and is_canonical != False


class TestCorrectionStrategy(unittest.TestCase):
    def test_correct_forms(self):
        citation_match = "1 ExD 123"
        citation_type = "PubNumAbbrNum"
        canonical_form = "d1 ExD d2"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation == citation_match
        assert year == ""

        citation_match = "[2025] EWHC 123 (TCC)"
        citation_type = "NCitYearAbbrNumDiv"
        canonical_form = "[dddd] EWHC d+ (TCC)"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation == citation_match
        assert year == "2025"

        citation_match = "[2024] EWCOP 758"
        citation_type = "NCitYearAbbrNum"
        canonical_form = "[dddd] EWCOP d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation == citation_match
        assert year == "2024"

        citation_match = "[1999] LGR 666"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] LGR d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation == citation_match
        assert year == "1999"

        citation_match = "Case T-123/12"
        citation_type = "EUTCase"
        canonical_form = "Case T-123/12"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation == citation_match
        assert year == ""

    def test_incorrect_forms(self):
        citation_match = "[2022] P.N.L.R 123"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] PNLR d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[2022] PNLR 123"
        assert year == "2022"

        citation_match = "(1995) 99 Cr. App. R. 123"
        citation_type = "PubYearNumAbbrNum"
        canonical_form = "(dddd) d1 Cr App R d2"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "(1995) 99 Cr App R 123"
        assert year == "1995"

        citation_match = "(2026) EWHC 789 (Fam)"
        citation_type = "NCitYearAbbrNumDiv"
        canonical_form = "[dddd] EWHC d+ (Fam)"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[2026] EWHC 789 (Fam)"
        assert year == "2026"

        citation_match = "[1999] A.C. 666"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] AC d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[1999] AC 666"
        assert year == "1999"

        citation_match = "[2019] Q.B. 456"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] QB d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type, citation_match, canonical_form
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[2019] QB 456"
        assert year == "2019"


class TestCitationReplacer(unittest.TestCase):
    """
    This class tests the replacement of the citations within the text itself. This comes from replacer.py
    """

    def test_citation_replacer(self):
        citation_match = "[2025] 1 All E.R. 123"  # incorrect citation
        corrected_citation = (
            "[2025] 1 All ER 123"  # in practice, returned via the citation matcher
        )
        year = "2025"
        URI = "#"
        is_neutral = "true"
        text = "In the judgment the incorrect citation is [2025] 1 All E.R. 123."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "[2022] UKET 789123_2012"
        corrected_citation = "[2022] UKET 789123/2012"
        year = "2022"
        URI = "#"
        is_neutral = "true"
        text = "This citation that needs to be changed is [2022] UKET 789123_2012 which discussed..."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "LR 1 A&E 123"
        corrected_citation = "LR 1 AE 123"
        year = "No Year"
        text = "LR 1 A&E 123 refers to..."
        URI = "#"
        is_neutral = "true"
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "(2022) EWHC 123 (Mercantile)"
        corrected_citation = "[2022] EWHC 123 (Mercantile)"
        year = "2022"
        URI = "#"
        is_neutral = "true"
        text = "I defer to the judgment in (2022) EWHC 123 (Mercantile)."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "[2022] ewca civ 123"
        corrected_citation = "[2022] EWCA Civ 123"
        year = "2022"
        URI = "#"
        is_neutral = "true"
        text = "[2022] ewca civ 123."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry


if __name__ == "__main__":
    unittest.main()
