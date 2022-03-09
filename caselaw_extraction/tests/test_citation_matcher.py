import unittest 
from spacy.lang.en import English
from correction_strategies import apply_correction_strategy
from replacer import replacer

CITATION_MATCH = []

# create mock function for the db connection 
# mock function to replicate the main file, without needing to use the xml files 
def mock_return_citation(nlp, text):
    doc = nlp(text)
    for ent in doc.ents:
        CITATION_MATCH.append(ent)
    return CITATION_MATCH 


class TestCitationProcessor(unittest.TestCase): 
    # TODO: 
    """
    1. verify that citation types are returned as expected
    3. verify extraction of year 
    4. verify canonical_form, descrption, and canonical form 
    5. verify matched rule? 
    6. verify replacer 
    7. verify correction strategy 
    verify with dummy strings om the different methods
    """
    def setUp(self): 
        super.setUp()
        self.nlp = English()
        self.nlp.max_length = 1500000
        citation_ruler = self.nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

    def test_corrected_citation():
        

    #def test_extracted_year():

