from tokenize import String
import unittest
from numpy import number 
from spacy.lang.en import English
from caselaw_extraction.correction_strategies import apply_correction_strategy
from caselaw_extraction.replacer import replacer
from caselaw_extraction.db_connection import create_connection, close_connection, get_matched_rule
from caselaw_extraction.helper import parse_file, load_patterns
import pandas as pd
import sqlite3
from sqlite3 import Error
import random


"""
    Testing the matching of the citations based on the data found in the rules. 
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

# current number of rules in the database
def get_rules_total(db_conn): 
    cursor = db_conn.cursor()
    number_of_rules = cursor.execute('''SELECT COUNT(*) FROM manifest''')
    number_of_rules = cursor.fetchone()
    number_of_rules = number_of_rules[0]  

    return number_of_rules


class TestCitationProcessor(unittest.TestCase): 
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
        
        self.nlp = English()
        self.nlp.max_length = 1500000
        self.nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

        self.db_conn = create_connection(DATABASE)
        load_patterns(self.db_conn)
    
    def test_parsing(self):
        correct_citations = ["random text goes here random text goes here **[2022] UKUT 177 (TCC)", "[2022] 1 Lloyd's Rep 123.", "..........Case C-123/12........" ]

        for text in correct_citations: 
            citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
            assert is_canonical == True
            assert citation_match is not None
            assert citation_type is not None
            assert canonical_form is not None
            assert description is not None


        text = "!!!!!!!_________[2047] Costs LR 123_____"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical == True

        text = "[2022] UKFTT 2020__0341 (GRC)"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical is None

    def test_correct_citations(self): 
        correct_citations = ["random text goes here [2022] 1 WLR 123 random text goes here",  "random text goes here random text goes here [2022] UKUT 123 (TCC)",  "random text [2004] AC 816 goes here  random text goes here "\
            "[2022] EWHC 123 (Pat)","......[2022] 1 QB 123......" ]

        for text in correct_citations: 
            citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
            assert is_canonical == True
            assert citation_match is not None
            assert citation_type is not None
            assert canonical_form is not None
            assert description is not None
        
       

    def test_corrected_citations(self):
        text = "random text goes here (2022) UKUT 123 (IAC) random text goes here"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical == False
        assert (type(canonical_form) is str)
        assert canonical_form == "[dddd] UKUT d+ (IAC)"
        assert citation_type == "NCitYearAbbrNumDiv"

        corrected_citation, year = apply_correction_strategy(citation_type, citation_match, canonical_form)
        assert year == "2022"
        assert corrected_citation == "[2022] UKUT 123 (IAC)"

        text = "[2057] A.C. 657 random text goes here"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical == False
        assert (type(canonical_form) is str)
        assert canonical_form == "[dddd] AC d+"
        assert citation_type == "PubYearAbbrNum"

        corrected_citation, year = apply_correction_strategy(citation_type, citation_match, canonical_form)
        assert year == "2057"
        assert corrected_citation == "[2057] AC 657"

        

    def test_unknown_citations(self):
        # Extra spaces
        text = "random text goes here random text goes here [2022] UKUT 177  (TCC)"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical != True and is_canonical != False
        
        text = "gCase C-123/12"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        assert is_canonical != True and is_canonical != False

        # citations to add - double brackets + () brackets or vice versa and malformed text between 


        
    def tearDown(self):
        close_connection(self.db_conn)

    

