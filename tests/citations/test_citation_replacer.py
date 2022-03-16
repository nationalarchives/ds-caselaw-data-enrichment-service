from tokenize import String
import unittest
from spacy.lang.en import English
from caselaw_extraction.correction_strategies import apply_correction_strategy
from caselaw_extraction.replacer import replacer
from caselaw_extraction.db_connection import create_connection, close_connection, get_matched_rule
from caselaw_extraction.helper import load_patterns

"""
    Testing the replacing of the citations in the sentences themselves. 
"""

DATABASE = "manifest.db"

# create mock function for the db connection 
# mock function to replicate the main file, without needing to use the xml files 
def mock_return_citation(nlp, text, db_conn):
    doc = nlp(text)
    citation_match = None
    is_canonical = None
    citation_type = None
    canonical_form = None
    description = None
    for ent in doc.ents:
        rule_id = ent.ent_id_
        citation_match = ent.text
        is_canonical, citation_type, canonical_form, description = get_matched_rule(db_conn, rule_id)
    return citation_match, is_canonical, citation_type, canonical_form, description


class TestCitationMatcher(unittest.TestCase): 
    def setUp(self): 
       
        self.nlp = English()
        self.nlp.max_length = 1500000
        self.nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

        self.db_conn = create_connection(DATABASE)
        load_patterns(self.db_conn)

    def test_corrected_citation(self):
        text = "random text goes here (2022) UKUT 123 (IAC) random text goes here"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        corrected_citation, year = apply_correction_strategy(citation_type, citation_match, canonical_form)
        # check the strings to ensure they have actually been replaced here 
        assert corrected_citation == "[2022] UKUT 123 (IAC)"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, corrected_citation, self.db_conn)
        assert is_canonical == True # Replaced citation should now be correct 
    
    def test_replaced_citation(self):
        texts = ["random test goes here... [1892] 1 QB 123....", "random test goes here... [1345] F.S.R. 123....", "refer to the case in (5674) 74 EHRR 123.", "also seen in [2022] R.P.C. 123..", \
            "see the judgment given in  (2045) UKFTT 143 (TC)"]
        for text in texts: 
            citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
            corrected_citation, year = apply_correction_strategy(citation_type, citation_match, canonical_form)
            replacement_entry = (citation_match, corrected_citation, year)
            replaced_entry = replacer(text, replacement_entry)
            assert corrected_citation in replaced_entry
            
        

    def tearDown(self):
        close_connection(self.db_conn)

    

