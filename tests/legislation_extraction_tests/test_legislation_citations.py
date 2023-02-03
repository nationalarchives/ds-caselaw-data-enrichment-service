import sys
import unittest

from numpy import mat
from spacy.lang.en import English

sys.path.append("./")
from legislation_processing.legislation_matcher_hybrid import (
    detect_year_span,
    detectCandidate,
    hybrid,
    leg_pipeline,
    lookup_pipe,
    mergedict,
    search_for_act,
    search_for_act_fuzzy,
)

from database.db_connection import (
    close_connection,
    create_connection,
    get_hrefs,
    get_legtitles,
)
from replacer.replacer import replacer_leg
from utils.helper import load_patterns

"""
    Testing the matching of legislation based on the data found in the lookup table. 
    These are independent unit tests.
"""


# creating a global set up to avoid duplicating
# logic normally handled in main.py
def set_up():
    nlp = English()
    nlp.max_length = 1500000
    db_conn = create_connection("tna", "editha.nemsic", "localhost", 5432)
    leg_titles = get_legtitles(db_conn)
    return nlp, db_conn, leg_titles


"""
    This class focuses on testing the Citation Processor, which gathers the results from the DB. This class primarily uses the mock_return_citation method.
    This includes testing incorrect or missing citations. 
    This is relevant for the logic performed in main.py
"""


class TestLegislationProcessor(unittest.TestCase):
    def setUp(self):
        self.nlp, self.db_conn, self.leg_titles = set_up()

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
        candidates = detectCandidate(self.nlp, doc)
        assert candidates == [(10, 12), (18, 20)]

        text = "(Act 2013) and can you find this [Act 2013]"
        doc = self.nlp(text)
        candidates = detectCandidate(self.nlp, doc)
        assert candidates == [(1, 3), (10, 12)]

        text = "(Act  2013) and can you find this [Act  2013]"
        doc = self.nlp(text)
        candidates = detectCandidate(self.nlp, doc)
        assert candidates == []

        text = "Act (2013) and can you find this"
        doc = self.nlp(text)
        candidates = detectCandidate(self.nlp, doc)
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

    def test_lookup_pipe(self):
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption Children Act 2002 requires the court, inter alia"
        doc = self.nlp(text)
        titles = ["Adoption and Children Act 2002", "Children and Families Act 2014"]
        cutoff = 90
        methods = {"exact": search_for_act, "hybrid": hybrid}
        results = lookup_pipe(
            titles, doc, self.nlp, methods["hybrid"], self.db_conn, cutoff
        )
        assert results == {
            "Adoption and Children Act 2002": [
                (
                    "Adoption Children Act 2002",
                    28,
                    32,
                    91,
                    "http://www.legislation.gov.uk/ukpga/2002/38",
                )
            ]
        }

    def tearDown(self):
        close_connection(self.db_conn)


"""
    This class tests the replacement of the citations within the text itself. This comes from replacer.py
"""


class TestLegislationReplacer(unittest.TestCase):
    def setUp(self):
        self.nlp, self.db_conn, self.leg_titles = set_up()

    def test_citation_replacer(self):
        legislation_match = "Adoption and Children Act 2002"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2002/38"
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption and Children Act 2002 requires the court, inter alia"
        replacement_entry = (legislation_match, href)
        replaced_entry = replacer_leg(text, replacement_entry)
        assert legislation_match in replaced_entry
        replacement_string = '<ref type="legislation" href="{}">{}</ref>'.format(
            href, legislation_match
        )
        print(replaced_entry)
        print(replacement_string)
        assert replacement_string in replaced_entry

        legislation_match = "Children and Families Act 2014"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2014/6/enacted"
        text = "In her first judgment on 31 January, the judge correctly directed herself as to the law, reminding herself that any application for expert evidence in children’s proceedings is governed by s.13 of the Children and Families Act 2014."
        replacement_entry = (legislation_match, href)
        replaced_entry = replacer_leg(text, replacement_entry)
        assert legislation_match in replaced_entry
        replacement_string = '<ref type="legislation" href="{}">{}</ref>'.format(
            href, legislation_match
        )
        print(replaced_entry)
        print(replacement_string)
        assert replacement_string in replaced_entry

    def tearDown(self):
        close_connection(self.db_conn)


if __name__ == "__main__":
    unittest.main()
