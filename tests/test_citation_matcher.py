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
       
        self.nlp = English()
        self.nlp.max_length = 1500000
        citation_ruler = self.nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

        self.db_conn = create_connection(DATABASE)
        load_patterns(self.db_conn)

    def test_correct_citations(self): 
        text = "random text goes here [2022] 1 WLR 123 random text goes here"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        print(is_canonical)
        assert is_canonical == True

        text = "random text goes here random text goes here [2022] UKUT 123 (TCC)"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        print(is_canonical)
        assert is_canonical == True

        text = "random text [2004] AC 816 goes here  random text goes here "
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        print(is_canonical)
        assert is_canonical == True

        # extra space in the citation - can't handle 
        """
        text = "random text goes here random text goes here [2022] UKUT 177  (TCC)"
        citation_match, is_canonical, citation_type, canonical_form, description = mock_return_citation(self.nlp, text, self.db_conn)
        print(is_canonical)
        assert is_canonical == True
        """
    def tearDown(self):
        close_connection(self.db_conn)

    #def test_corrected_citation(self):
       # text = "random text goes here [2004] 1 AC 816 random text goes here"

    #def test_extracted_year():

