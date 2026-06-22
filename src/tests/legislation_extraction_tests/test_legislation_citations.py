"""
Testing the matching of legislation based on the data found in the lookup table.
These are independent unit tests.
"""

from enrichment.legislation_extraction.legislation_matcher_hybrid import (
    detect_candidates,
    detect_year_span,
    lookup_pipe,
    resolve_overlap,
    search_for_act_fuzzy,
)
from enrichment.legislation_extraction.legislation_matcher_hybrid import (
    exact_matcher as search_for_act,
)
from enrichment.legislation_extraction.legislation_matcher_hybrid import (
    fuzzy_matcher as hybrid,
)


class TestResolveOlverlap:
    def test_resolve_overlap_without_overlap(self):
        results = {
            "Adoption and Children Act 2002": [
                ("Adoption Children Act 2002", 1, 3, 91, "http://www.legislation.gov.uk/ukpga/2002/38", "citation_abc"),
                ("Adopted Children Act 2002", 11, 33, 4, "http://www.legislation.gov.uk/ukpga/2011/38", "citation_abc"),
                (
                    "Adoption of Children Act 2002",
                    111,
                    333,
                    3,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "citation_abc",
                ),
            ],
        }

        assert resolve_overlap(results) == results

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
            ],
        }

        pruned = resolve_overlap(results)

        assert pruned == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption of Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2022/38",
                    "citation_abc",
                ),
            ],
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
                ("Adopted Children Act 2002", 28, 32, 3, "http://www.legislation.gov.uk/ukpga/2011/38", "citation_abc"),
                ("Adoption of Children Act 2002", 28, 32, 4, "http://www.legislation.gov.uk/ukpga/2022/38", "t"),
            ],
        }

        pruned = resolve_overlap(results)

        assert pruned == {
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
                ("Adopted Children Act 2002", 28, 32, 3, "http://www.legislation.gov.uk/ukpga/2011/38", "citation_abc"),
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

        assert resolve_overlap(results) == {
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


def test_lookup_pipe(nlp, db_connection, seed_ukpga_lookup):
    text = (
        "In their skeleton argument in support of the first ground, "
        "Mr Goodwin and Mr Redmond remind the court that the welfare checklist "
        "in s.1(4) of the Adoption Children Act 2002 requires the court"
    )

    doc = nlp(text)
    titles = ["Adoption and Children Act 2002", "Children and Families Act 2014"]
    cutoff = 90

    results = lookup_pipe(
        titles,
        doc,
        nlp,
        hybrid,
        db_connection,
        cutoff,
    )

    assert results == {
        "Adoption and Children Act 2002": [
            ("Adoption Children Act 2002", 28, 32, 91, "http://www.legislation.gov.uk/ukpga/2002/38", "citation_abc"),
        ],
    }


# ---------------- helpers ----------------


def test_detect_year_span(nlp):
    doc = nlp("!!!!!!!_________Adoption and Children Act 2002_____")
    assert detect_year_span(doc, nlp) == {2002}

    doc = nlp("Adoption and Children Act .2002..")
    assert detect_year_span(doc, nlp) == set()

    doc = nlp("[2022] UKFTT 2020__0341 (GRC)")
    assert detect_year_span(doc, nlp) == {2022}

    doc = nlp("what [2022] 2017 placeholder text 2013 and 1974")
    assert detect_year_span(doc, nlp) == {2022, 2017, 2013, 1974}


def test_detect_candidates(nlp):
    doc = nlp("checking if the code will find this Made-up Act 1987 and this second made-up Act 2013")
    assert detect_candidates(nlp, doc) == [(10, 12), (18, 20)]

    doc = nlp("(Act 2013) and can you find this [Act 2013]")
    assert detect_candidates(nlp, doc) == [(1, 3), (10, 12)]

    doc = nlp("(Act  2013) and can you find this [Act  2013]")
    assert detect_candidates(nlp, doc) == []

    doc = nlp("Act (2013) and can you find this")
    assert detect_candidates(nlp, doc) == []


def test_search_for_act(nlp):
    text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption and Children Act 2002 requires the court, inter alia"
    doc = nlp(text)
    title = "Adoption and Children Act 2002"
    matched_text = search_for_act(title, doc, nlp)
    assert matched_text == [("Adoption and Children Act 2002", 28, 33, 100)]

    text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
    doc = nlp(text)
    title = "Adoption and Children Act 2002"
    matched_text = search_for_act(title, doc, nlp)
    assert matched_text == []


def test_search_for_act_fuzzy(nlp):
    text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
    doc = nlp(text)

    assert search_for_act_fuzzy(
        "Adoption and Children Act 2002",
        doc,
        nlp,
        90,
    ) == [
        ("Adoption Children Act 2002", 28, 32, 93),
    ]


def test_hybrid(nlp):
    text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
    doc = nlp(text)

    candidates = [(30, 32)]

    assert hybrid(
        "Adoption and Children Act 2002",
        doc,
        nlp,
        90,
        candidates,
    ) == [
        ("Adoption Children Act 2002", 28, 32, 91),
    ]
