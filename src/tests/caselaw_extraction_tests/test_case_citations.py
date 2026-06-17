"""
Testing the matching of the citations based on the data found in the rules.
These are independent unit tests.
"""

import pytest

from caselaw_extraction.correction_strategies import apply_correction_strategy
from database.db_connection import get_matched_rule

CORRECT_CITATIONS = [
    "random text goes here random text goes here **[2022] UKUT 177 (TCC)",
    "[2022] 1 Lloyd's Rep 123.",
    "..........Case C-123/12........",
    "[[2022] EWHC 123 (Mercantile) ",
    "[2022] EWHC 123 (TCC))",
    "random text goes here [2022] 1 WLR 123 random text goes here",
    "random text goes here random text goes here [2022] UKUT 123 (TCC)",
    "random text [2004] AC 816 goes here  random text goes here [2022] EWHC 123 (Pat)",
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


@pytest.mark.integration
class TestCitationProcessor:
    """
    Tests the Citation Processor, which resolves citations from the database.

    Focus:
    - spaCy entity matching
    - DB-backed citation resolution
    - correctness of canonical / non-canonical classification
    """

    def test_citation_matching(self, nlp, db_connection, manifest_table):
        text = "!!!!!!!_________[2047] Costs LR 123_____"

        (
            citation_match,
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = mock_return_citation(nlp, text, db_connection)

        assert is_canonical is True

        text = "[2022] UKFTT 2020__0341 (GRC)"

        (
            citation_match,
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = mock_return_citation(nlp, text, db_connection)

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
        ) = mock_return_citation(nlp, text, db_connection)

        assert is_canonical is True

    def test_correct_canonical(self, nlp, db_connection, manifest_table):
        for text in CORRECT_CITATIONS:
            _, _, _, _, is_canonical, _, _ = mock_return_citation(
                nlp,
                text,
                db_connection,
            )
            assert is_canonical is True

    def test_citation_type_found(self, nlp, db_connection, manifest_table):
        for text in CORRECT_CITATIONS:
            _, _, _, _, _, citation_type, _ = mock_return_citation(
                nlp,
                text,
                db_connection,
            )
            assert citation_type is not None

    def test_canonical_form_found(self, nlp, db_connection, manifest_table):
        for text in CORRECT_CITATIONS:
            _, _, _, _, _, _, canonical_form = mock_return_citation(
                nlp,
                text,
                db_connection,
            )
            assert canonical_form is not None

    def test_incorrect_canonical_form(self, nlp, db_connection, manifest_table):
        for text in INCORRECT_CITATIONS:
            _, _, _, _, is_canonical, _, canonical_form = mock_return_citation(
                nlp,
                text,
                db_connection,
            )

            assert is_canonical is False
            assert isinstance(canonical_form, str)

    def test_incorrect_citation_match(self, nlp, db_connection, manifest_table):
        for text in INCORRECT_CITATIONS:
            citation_match, _, _, _, _, _, _ = mock_return_citation(
                nlp,
                text,
                db_connection,
            )

            assert citation_match is not None

    def test_unknown_citations(self, nlp, db_connection, manifest_table):
        for text in UNKNOWN_CITATIONS:
            _, _, _, _, is_canonical, _, _ = mock_return_citation(
                nlp,
                text,
                db_connection,
            )

            assert is_canonical not in (True, False)


class TestCorrectionStrategy:
    def test_correct_forms(self):
        citation_match = "1 ExD 123"
        citation_type = "PubNumAbbrNum"
        canonical_form = "d1 ExD d2"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation == citation_match
        assert year == ""

        citation_match = "[2025] EWHC 123 (TCC)"
        citation_type = "NCitYearAbbrNumDiv"
        canonical_form = "[dddd] EWHC d+ (TCC)"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation == citation_match
        assert year == "2025"

        citation_match = "[2024] EWCOP 758"
        citation_type = "NCitYearAbbrNum"
        canonical_form = "[dddd] EWCOP d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation == citation_match
        assert year == "2024"

        citation_match = "[1999] LGR 666"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] LGR d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation == citation_match
        assert year == "1999"

        citation_match = "Case T-123/12"
        citation_type = "EUTCase"
        canonical_form = "Case T-123/12"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation == citation_match
        assert year == ""

    def test_incorrect_forms(self):
        citation_match = "[2022] P.N.L.R 123"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] PNLR d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[2022] PNLR 123"
        assert year == "2022"

        citation_match = "(1995) 99 Cr. App. R. 123"
        citation_type = "PubYearNumAbbrNum"
        canonical_form = "(dddd) d1 Cr App R d2"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "(1995) 99 Cr App R 123"
        assert year == "1995"

        citation_match = "(2026) EWHC 789 (Fam)"
        citation_type = "NCitYearAbbrNumDiv"
        canonical_form = "[dddd] EWHC d+ (Fam)"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[2026] EWHC 789 (Fam)"
        assert year == "2026"

        citation_match = "[1999] A.C. 666"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] AC d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[1999] AC 666"
        assert year == "1999"

        citation_match = "[2019] Q.B. 456"
        citation_type = "PubYearAbbrNum"
        canonical_form = "[dddd] QB d+"
        corrected_citation, year, d1, d2 = apply_correction_strategy(
            citation_type,
            citation_match,
            canonical_form,
        )
        assert corrected_citation != citation_match
        assert corrected_citation == "[2019] QB 456"
        assert year == "2019"
