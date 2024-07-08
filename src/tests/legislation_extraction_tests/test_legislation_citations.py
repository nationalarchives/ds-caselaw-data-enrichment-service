import unittest

import psycopg2
import testing.postgresql
from spacy.lang.en import English

from legislation_extraction.legislation_matcher_hybrid import (
    detect_candidates,
    detect_year_span,
    lookup_pipe,
    resolve_overlap,
    search_for_act_fuzzy,
)
from legislation_extraction.legislation_matcher_hybrid import (
    exact_matcher as search_for_act,
)
from legislation_extraction.legislation_matcher_hybrid import (
    fuzzy_matcher as hybrid,
)

"""
    Testing the matching of legislation based on the data found in the lookup table.
    These are independent unit tests.
"""


class TestLegislationProcessor(unittest.TestCase):
    def setUp(self):
        self.nlp = English()
        self.nlp.max_length = 1500000
        self.postgresql = testing.postgresql.Postgresql()
        self.db_conn = psycopg2.connect(**self.postgresql.dsn())

        sql_query = """
        CREATE TABLE ukpga_lookup (
            candidate_titles VARCHAR(100) NOT NULL,
            ref VARCHAR(100) NOT NULL,
            citation VARCHAR(100) NOT NULL,
            year BIGINT NOT NULL,
            for_fuzzy BOOLEAN NOT NULL
        );
        INSERT INTO ukpga_lookup (candidate_titles, ref, citation, year, for_fuzzy)
        VALUES
            ('Adoption and Children Act 2002', 'http://www.legislation.gov.uk/ukpga/2002/38', 'citation_abc', 2002, true),
            ('def', 'ref_def', 'citation_def', 2001, true),
            ('ghi', 'ref_ghi', 'citation_ghi', 2002, false);
        """

        cursor = self.db_conn.cursor()
        cursor.execute(sql_query)

    def tearDown(self):
        self.postgresql.stop()

    def test_resolve_overlap_without_overlap(self):
        results = {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    1,
                    3,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "citation_abc",
                ),
                (
                    "Adopted Children Act 2002",
                    11,
                    33,
                    4,
                    "http://www.legislation.gov.uk/ukpga/2011/38",
                    "citation_abc",
                ),
                (
                    "Adoption of Children Act 2002",
                    111,
                    333,
                    3,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "citation_abc",
                ),
            ]
        }
        pruned_results = resolve_overlap(results)

        assert pruned_results == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    1,
                    3,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "citation_abc",
                ),
                (
                    "Adopted Children Act 2002",
                    11,
                    33,
                    4,
                    "http://www.legislation.gov.uk/ukpga/2011/38",
                    "citation_abc",
                ),
                (
                    "Adoption of Children Act 2002",
                    111,
                    333,
                    3,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "citation_abc",
                ),
            ]
        }

    def test_resolve_overlap_with_overlap_returns_last_one_if_all_equally_good(self):
        results = {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "citation_abc",
                ),
                (
                    "Adopted Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2011/38",
                    "citation_abc",
                ),
                (
                    "Adoption of Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "citation_abc",
                ),
            ]
        }
        pruned_results = resolve_overlap(results)

        assert pruned_results == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption of Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "citation_abc",
                ),
            ]
        }

    def test_resolve_overlap_with_overlap_returns_best_one(self):
        results = {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    100,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "this_is_the_best",
                ),
                (
                    "Adopted Children Act 2002",
                    28,
                    32,
                    3,
                    "http://www.legislation.gov.uk/ukpga/2011/38",
                    "citation_abc",
                ),
                (
                    "Adoption of Children Act 2002",
                    28,
                    32,
                    4,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "t",
                ),
            ]
        }
        pruned_results = resolve_overlap(results)

        assert pruned_results == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    100,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "this_is_the_best",
                ),
            ]
        }

    def test_resolve_overlap_with_overlap_and_no_overlap(self):
        results = {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    100,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "this_is_the_best",
                ),
                (
                    "Adopted Children Act 2002",
                    28,
                    32,
                    3,
                    "http://www.legislation.gov.uk/ukpga/2011/38",
                    "citation_abc",
                ),
            ],
            "Completely Unrelated Act 1999": [
                (
                    "Completely Unrelated Act 1999",
                    99,
                    99,
                    99,
                    "http://www.legislation.gov.uk/ukut/2022/38",
                    "citation_xyz",
                ),
            ],
        }
        pruned_results = resolve_overlap(results)

        assert pruned_results == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    100,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "this_is_the_best",
                ),
            ],
            "Completely Unrelated Act 1999": [
                (
                    "Completely Unrelated Act 1999",
                    99,
                    99,
                    99,
                    "http://www.legislation.gov.uk/ukut/2022/38",
                    "citation_xyz",
                ),
            ],
        }

    def test_lookup_pipe(self):
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
        doc = self.nlp(text)
        titles = ["Adoption and Children Act 2002", "Children and Families Act 2014"]
        cutoff = 90
        methods = {"exact": search_for_act, "hybrid": hybrid}
        results = lookup_pipe(titles, doc, self.nlp, methods["hybrid"], self.db_conn, cutoff)

        assert results == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                    "citation_abc",
                )
            ]
        }


class TestLegislationProcessorHelpers(unittest.TestCase):
    def setUp(self):
        self.nlp = English()
        self.nlp.max_length = 1500000

    # Handling extra characters around the citations to ensure that spacy handles it well
    def test_detect_year_span(self):
        # including additional text around the citation to handling the parsing
        text = "!!!!!!!_________Adoption and Children Act 2002_____"
        doc = self.nlp(text)
        dates = detect_year_span(doc, self.nlp)
        assert dates == {2002}

        text = "Adoption and Children Act .2002.."
        doc = self.nlp(text)
        dates = detect_year_span(doc, self.nlp)
        assert len(dates) == 0

        text = "[2022] UKFTT 2020__0341 (GRC)"
        doc = self.nlp(text)
        dates = detect_year_span(doc, self.nlp)
        assert dates == {2022}

        text = "what [2022] 2017 placeholder text 2013 and 1974"
        doc = self.nlp(text)
        dates = detect_year_span(doc, self.nlp)
        assert dates == {2022, 2017, 2013, 1974}

    # for correct citations - ensure it finds that it is canonical
    def test_detect_candidate(self):
        text = "checking if the code will find this Made-up Act 1987 and this second made-up Act 2013"
        doc = self.nlp(text)
        candidates = detect_candidates(self.nlp, doc)
        assert candidates == [(10, 12), (18, 20)]

        text = "(Act 2013) and can you find this [Act 2013]"
        doc = self.nlp(text)
        candidates = detect_candidates(self.nlp, doc)
        assert candidates == [(1, 3), (10, 12)]

        text = "(Act  2013) and can you find this [Act  2013]"
        doc = self.nlp(text)
        candidates = detect_candidates(self.nlp, doc)
        assert candidates == []

        text = "Act (2013) and can you find this"
        doc = self.nlp(text)
        candidates = detect_candidates(self.nlp, doc)
        assert candidates == []

    def test_search_for_act(self):
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption and Children Act 2002 requires the court, inter alia"
        doc = self.nlp(text)
        title = "Adoption and Children Act 2002"
        matched_text = search_for_act(title, doc, self.nlp)
        assert matched_text == [("Adoption and Children Act 2002", 28, 33, 100)]

        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
        doc = self.nlp(text)
        title = "Adoption and Children Act 2002"
        matched_text = search_for_act(title, doc, self.nlp)
        assert matched_text == []

    def test_search_for_act_fuzzy(self):
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
        doc = self.nlp(text)
        title = "Adoption and Children Act 2002"
        cutoff = 90
        matched_text = search_for_act_fuzzy(title, doc, self.nlp, cutoff)
        assert matched_text == [("Adoption Children Act 2002", 28, 32, 93)]

    def test_hybrid(self):
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
        doc = self.nlp(text)
        title = "Adoption and Children Act 2002"
        cutoff = 90
        candidates = [(30, 32)]
        all_matches = hybrid(title, doc, self.nlp, cutoff, candidates)
        assert all_matches == [("Adoption Children Act 2002", 28, 32, 91)]


if __name__ == "__main__":
    unittest.main()
