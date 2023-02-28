"""
    This test file looks at the matching of different abbreviations. 

    Note that the current abbreviation pipeline currently only supports abbreviations 
    where the abbreviation in brackets is in quotation marks, which this file will 
    also test for. If this is updated, this will need to be reflected in the tests. 
"""
import sys
import unittest

import spacy
from spacy.language import Language

sys.path.append("./")

from abbreviation_extraction.abbreviations import (
    AbbreviationDetector,
    filter_matches,
    find_abbreviation,
)
from replacer.replacer import replacer_abbr


@Language.factory("abbreviation_detector")
def create_abbreviation_detector(nlp, name: str):
    return AbbreviationDetector(nlp)

class TestFindAbbreviation(unittest.TestCase):
    """Unit Tests for `find_abbreviation`"""

    def setUp(self):
        self.nlp = spacy.load(
            "en_core_web_sm",
            exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"],
        )
        self.nlp.add_pipe("abbreviation_detector")

    def test_find_abbreviation(self):
        """
        Given a spaCy span of text
        And a corresponding span of text representing an abbreviation
        When find_abbreviation is called with them
        Then a tuple of spans is returned including the short form, long form
        """
        text = 'Upper Tribunal ("UT") '
        doc = self.nlp(text)
        long = doc[0:2]
        short = doc[3:6]

        short_form, long_form = find_abbreviation(long, short)
        assert short_form.text == '"UT"'
        assert long_form.text == "Upper Tribunal"

    def test_find_abbreviation_with_date(self):
        """
        Given a spaCy span of text with date
        And a corresponding span of text representing an abbreviation
        When find_abbreviation is called with them
        Then a tuple of spans is returned including the short form, long form
        """
        text = 'The provision is found in the Companies Act 2006 ("CA 2006")'
        doc = self.nlp(text)
        long = doc[6:9]
        short = doc[10:14]

        short_form, long_form = find_abbreviation(long, short)
        assert short_form.text == '"CA 2006"'
        assert long_form.text == "Companies Act 2006"

    @unittest.skip("abbreviations_with_prefix_currently_not_found")
    def test_find_abbreviation_with_prefix(self):
        """
        Given a spaCy span of text with prefix
        And a corresponding span of text representing an abbreviation
        When find_abbreviation is called with them
        Then a tuple of spans is returned including the short form, long form
        """
        text = 'section 17 of the Value Added Tax Act ("the VAT Act") '
        doc = self.nlp(text)
        long = doc[4:8]
        short = doc[9:13]

        short_form, long_form = find_abbreviation(long, short)
        assert short_form.text == '"the VAT Act"'
        assert long_form.text == "Value Added Tax Act"


class TestFilterMatches(unittest.TestCase):
    def setUp(self):
        self.nlp = spacy.load(
            "en_core_web_sm",
            exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"],
        )

        self.nlp.add_pipe("abbreviation_detector")

    def test_short_form(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then a list of tuples of long_form, short_form spans
        """
        text = 'European Economic Area ("EEA")'
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)

        long_form_candidate = filtered[0][0]
        short_form_candidate = filtered[0][1]
        assert long_form_candidate.text == "European Economic Area"
        assert short_form_candidate.text == "EEA"

    def test_short_form_with_date(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then a list of tuples of long_form, short_form spans
        """
        text = 'Companies Act 2006 ("CA 2006")'
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 8)], doc)

        long_form_candidate = filtered[0][0]
        short_form_candidate = filtered[0][1]
        assert long_form_candidate.text == "Companies Act 2006"
        assert short_form_candidate.text == "CA 2006"

    @unittest.skip("abbreviations_with_prefix_currently_not_found")
    def test_short_form_with_prefix(self):
        text = 'Value Added Tax Act ("the VAT Act") '
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 10)], doc)

        short_form_candidate = filtered[0][1]
        long_form_candidate = filtered[0][0]
        assert short_form_candidate.text == "the VAT Act"
        assert long_form_candidate.text == "Value Added Tax Act"

    @unittest.skip("abbreviations_with_prefix_currently_not_found")
    def test_with_quotations_and_prefix(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form is enclosed by quotes
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then a list of tuples of long_form, short_form spans
        """
        text = "Value Added Tax Act ('the VAT Act') "
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 10)], doc)

        short_form_candidate = filtered[0][1]
        long_form_candidate = filtered[0][0]
        assert short_form_candidate.text == "the VAT Act"
        assert long_form_candidate.text == "Value Added Tax Act"

    def test_with_double_quotes(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form is enclosed by double quotes
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then a list of tuples of long_form, short_form spans
        """
        text = 'European Economic Area ("EEA")'
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)

        short_form_candidate = filtered[0][1]
        long_form_candidate = filtered[0][0]
        assert short_form_candidate.text == "EEA"
        assert long_form_candidate.text == "European Economic Area"

    def test_with_forward_quotes(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form is enclosed by forward quotes
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then a list of tuples of long_form, short_form spans
        """
        text = "European Economic Area (‘EEA‘)"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)

        short_form_candidate = filtered[0][1]
        long_form_candidate = filtered[0][0]
        assert short_form_candidate.text == "EEA"
        assert long_form_candidate.text == "European Economic Area"

    def test_with_double_forward_quotes(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form is enclosed by double forward quotes
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then a list of tuples of long_form, short_form spans
        """
        text = "European Economic Area (“EEA“)"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)

        short_form_candidate = filtered[0][1]
        long_form_candidate = filtered[0][0]
        assert short_form_candidate.text == "EEA"
        assert long_form_candidate.text == "European Economic Area"

    def test_no_quotations(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form is enclosed by no quotes
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then an empty list is returned
        """
        text = "European Economic Area (EEA)"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        assert len(filtered) == 0

    def test_no_quotations_but_quotes_in_long_form(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form is enclosed by no quotes but there a
            quotes in the long form
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then an empty list is returned
        """
        text = 'section 6 of the "Human Rights Act 1998" (the HRA 1998)'
        doc = self.nlp(text)
        filtered = filter_matches([(5, 11, 15)], doc)
        assert len(filtered) == 0

    def test_only_one_quotation_will_not_count_as_abbreviation(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            where the short form has only one quotation mark
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then an empty list is returned
        """
        text = 'Value Added Tax Act (the VAT Act") '
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 9)], doc)
        assert len(filtered) == 0

    def test_apostrophes_will_not_count_as_abbreviation(self):
        """
        Given a spaCy doc of text of form "<Long Form> (<Short Form>)"
            with apostrophes
        And a list of matcher_output of form [(abbreviation_match_number, start, end)]
        When find_abbreviation is called with them
        Then an empty list is returned
        """
        text = "at the doctor's office (the doctor's office) "
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 9)], doc)
        assert len(filtered) == 0


class TestReplacerAbbr(unittest.TestCase):
    """Unit Tests for `replacer_abbr`"""

    def test_replacer_abbr(self):
        """
        Given a text string and a tuple of original string and abbreviation
            where the original string is contained in the text string
        When replacer_abbr is called with these
        Then a string is returned that looks like the original text string
            with the matching string enclosed by an <abbr> tag with the replacement
            string as the title attribute and TNA as the uk:origin attribute
        """
        text = "This game requires 12 GB of Random Access Memory"
        replacement_entry = ("Random Access Memory", "RAM")

        expected = (
            "This game requires 12 GB of "
            '<abbr title="RAM" uk:origin="TNA">'
            "Random Access Memory"
            "</abbr>"
        )
        assert replacer_abbr(text, replacement_entry) == expected


if __name__ == "__main__":
    unittest.main()
