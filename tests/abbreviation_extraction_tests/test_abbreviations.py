import unittest
import sys

from numpy import short
sys.path.append("./")
from abbreviation_extraction.abbreviations import AbbreviationDetector, find_abbreviation, filter_matches
import spacy 
from spacy.language import Language
from spacy.tokens import Span, Doc
from spacy.matcher import Matcher
"""
    This test file looks at the matching of different abbreviations. 

    Note that the current abberviation pipeline currently only supports abbreviations 
    where the abbreviation in brackets is in quotation marks, which this file will 
    also test for. If this is updated, this will need to be reflected in the tests. 
"""

class TestAbbrevationMatcher(unittest.TestCase): 
    def setUp(self): 
        self.nlp = spacy.load("en_core_web_sm", exclude=['tok2vec', 'attribute_ruler', 'lemmatizer', 'ner'])

        @Language.factory("abbreviation_detector")
        def create_abbreviation_detector(nlp, name: str): 
            return AbbreviationDetector(nlp)

        self.nlp.add_pipe("abbreviation_detector") 
        self.text = "The European Court of Human Rights (\"ECtHR\") was set up in 1959, it is based in Strasbourg"
    
    def test_long_form(self): 
        # test that the long forms are being parsed and found correctly by find_abbreviations
        text = "The provision is found in the Companies Act 2006 (\"CA 2006\")"
        doc = self.nlp(text)
        long = doc[6:9]
        short = doc[10:14]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Companies Act 2006"

        text = "Upper Tribunal (\"UT\") "
        doc = self.nlp(text)
        long = doc[0:2]
        short = doc[3:5]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Upper Tribunal"

        text = "section 17 of the Value Added Tax Act (\"the VAT Act\") "
        doc = self.nlp(text)
        long = doc[4:8]
        short = doc[9:13]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Value Added Tax Act"
    
    def test_short_form(self): 
        # test that the short forms are being parsed and found correctly by filter_matches
        text = "Companies Act 2006 (\"CA 2006\")"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 8)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "CA 2006"

        text = "European Economic Area (\"EEA\")"
        doc = self.nlp(text)
        filtered = filter_matches([(1, 4, 7)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "EEA"

        text = "Value Added Tax Act (\"the VAT Act\") "
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 10)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "the VAT Act"

    # testing that different quotations are supported and the short forms are identified 
    def test_quotations(self): 
        # single quotes
        text = "Value Added Tax Act (\'the VAT Act\') "
        doc = self.nlp(text)
        filtered = filter_matches([(1, 5, 10)], doc)
        short_form_candidate = filtered[0][1]
        assert short_form_candidate.text == "the VAT Act"

        # double quotes
        text = "European Economic Area (\"EEA\")"
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


    
if __name__ == '__main__':
    unittest.main()
