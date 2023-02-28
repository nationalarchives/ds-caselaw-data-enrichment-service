import sys
import unittest

sys.path.append("./")
import spacy
from spacy.language import Language

from abbreviation_extraction.abbreviations import (
    AbbreviationDetector,
    filter_matches,
    find_abbreviation,
)
from replacer.replacer import replacer_abbr

"""
    This test file looks at the matching of different abbreviations.

    Note that the current abberviation pipeline currently only supports abbreviations
    where the abbreviation in brackets is in quotation marks, which this file will
    also test for. If this is updated, this will need to be reflected in the tests.
"""


class TestAbbrevationMatcher(unittest.TestCase):
    def setUp(self):
        self.nlp = spacy.load(
            "en_core_web_sm",
            exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"],
        )

        @Language.factory("abbreviation_detector")
        def create_abbreviation_detector(nlp, name: str):
            return AbbreviationDetector(nlp)

        self.nlp.add_pipe("abbreviation_detector")

    def test_long_form(self):
        # test that the long forms are being parsed and found correctly by find_abbreviations
        text = 'The provision is found in the Companies Act 2006 ("CA 2006")'
        doc = self.nlp(text)
        long = doc[6:9]
        short = doc[10:14]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Companies Act 2006"

        text = 'Upper Tribunal ("UT") '
        doc = self.nlp(text)
        long = doc[0:2]
        short = doc[3:5]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Upper Tribunal"

        text = 'section 17 of the Value Added Tax Act ("the VAT Act") '
        doc = self.nlp(text)
        long = doc[4:8]
        short = doc[9:13]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Value Added Tax Act"

    def test_short_form(self):
        # test that the short forms are being parsed and found correctly by filter_matches
        text = 'Companies Act 2006 ("CA 2006")'
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 8)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "CA 2006"

        text = 'European Economic Area ("EEA")'
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "EEA"

        text = 'Value Added Tax Act ("the VAT Act") '
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 10)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "the VAT Act"

    # testing that different quotations are supported and the short forms are identified
    def test_quotations(self):
        # single quotes
        text = "Value Added Tax Act ('the VAT Act') "
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 10)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "the VAT Act"

        # double quotes
        text = 'European Economic Area ("EEA")'
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "EEA"

        text = "European Economic Area (‘EEA‘)"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "EEA"

        text = "European Economic Area (“EEA“)"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "EEA"

    # testing that different abbreviations without quotations in their brackets are not parsed correctly
    def test_no_quotations(self):
        text = "European Economic Area (EEA)"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        # no matches are returned and therefore length is 0
        assert len(filtered) == 0

        # check that quotes in the long form don't interefere
        text = 'section 6 of the "Human Rights Act 1998" (the HRA 1998)'
        doc = self.nlp(text)
        filtered = filter_matches([(5, 11, 15)], doc)
        # no matches are returned and therefore length is 0
        assert len(filtered) == 0

        # only one quotation mark will not be counted as an abbreviation
        text = 'Value Added Tax Act (the VAT Act") '
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 9)], doc)
        # no matches are returned and therefore length is 0
        assert len(filtered) == 0

        # apostrophe will not count as an abbreviation
        text = "at the doctor's office (the doctor's office) "
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 9)], doc)
        # no matches are returned and therefore length is 0
        assert len(filtered) == 0


class TestAbbrevationReplacer(unittest.TestCase):
    # text XML replacements of the short form
    def test_abbreviation_replacer_short_form(self):
        long_form = "European Court of Human Rights"
        short_form = "ECHR"
        replacement_entry = (short_form, long_form)
        text = "The case was heard before the ECHR"
        replacement_string = 'The case was heard before the <abbr title="{}" uk:origin="TNA">{}</abbr>'.format(
            long_form, short_form
        )
        replaced_entry = replacer_abbr(text, replacement_entry)
        assert short_form in replaced_entry
        assert long_form in replaced_entry
        assert replacement_string in replaced_entry

        long_form = "Human Rights Act 1998"
        short_form = "the HRA 1998"
        replacement_entry = (short_form, long_form)
        text = "in breach of section 6 of the HRA 1998"
        replacement_string = 'in breach of section 6 of <abbr title="{}" uk:origin="TNA">{}</abbr>'.format(
            long_form, short_form
        )
        replaced_entry = replacer_abbr(text, replacement_entry)
        assert short_form in replaced_entry
        assert long_form in replaced_entry
        assert replacement_string in replaced_entry

        long_form = "1980 Hague Child Abduction Convention"
        short_form = "1980 Convention"
        replacement_entry = (short_form, long_form)
        text = "This concerns a return order made under the 1980 Convention on 38th October"
        replacement_string = 'This concerns a return order made under the <abbr title="{}" uk:origin="TNA">{}</abbr> on 38th October'.format(
            long_form, short_form
        )
        replaced_entry = replacer_abbr(text, replacement_entry)
        assert short_form in replaced_entry
        assert long_form in replaced_entry
        assert replacement_string in replaced_entry

    # reverse of the above, where it is the long form previously defined in quotes in brackets
    def test_abbreviation_replacer_long_form(self):
        long_form = "Family Procedure Rules 2010"
        short_form = "FPR 2010"
        replacement_entry = (long_form, short_form)
        text = "Family Procedure Rules 2010"
        replacement_string = '<abbr title="{}" uk:origin="TNA">{}</abbr>'.format(
            short_form, long_form
        )
        replaced_entry = replacer_abbr(text, replacement_entry)
        assert short_form in replaced_entry
        assert long_form in replaced_entry
        assert replacement_string in replaced_entry

        long_form = "Canadian Geese Limited"
        short_form = "Canadian Geese"
        replacement_entry = (long_form, short_form)
        text = "This case concerns Canadian Geese Limited"
        replacement_string = (
            'This case concerns <abbr title="{}" uk:origin="TNA">{}</abbr>'.format(
                short_form, long_form
            )
        )
        replaced_entry = replacer_abbr(text, replacement_entry)
        assert short_form in replaced_entry
        assert long_form in replaced_entry
        assert replacement_string in replaced_entry

        long_form = "Special Immigration Appeals Commission Act 1997 "
        short_form = "the 1997 Act"
        replacement_entry = (long_form, short_form)
        text = "the Special Immigration Appeals Commission Act 1997 "
        replacement_string = 'the <abbr title="{}" uk:origin="TNA">{}</abbr>'.format(
            short_form, long_form
        )
        replaced_entry = replacer_abbr(text, replacement_entry)
        assert short_form in replaced_entry
        assert long_form in replaced_entry
        assert replacement_string in replaced_entry


if __name__ == "__main__":
    unittest.main()
