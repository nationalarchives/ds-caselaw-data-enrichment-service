import unittest
import sys
sys.path.append("./")
from abbreviation_extraction.abbreviations import AbbreviationDetector, find_abbreviation
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

        text = "The provision is found in the Companies Act 2006 (\"CA 2006\")"
        doc = self.nlp(text)
        long = doc[6:9]
        short = doc[10:14]
        _, long_form = find_abbreviation(long, short)
        assert long_form.text == "Companies Act 2006"

    
if __name__ == '__main__':
    unittest.main()
