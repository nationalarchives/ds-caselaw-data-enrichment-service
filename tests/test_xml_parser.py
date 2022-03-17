import unittest
from caselaw_extraction.helper import load_pattern, parse_file
from spacy.lang.en import English
import sys
sys.path.append("./")
from caselaw_extraction.correction_strategies import apply_correction_strategy
from caselaw_extraction.db_connection import create_connection, close_connection, get_matched_rule
from caselaw_extraction.helper import load_patterns
from caselaw_extraction.replacer import replacer

"""
    Testing the xml parser to ensure that information is extracted as expected. 
"""

DATABASE = "manifest.db"

def set_up():
    nlp = English()
    nlp.max_length = 1500000
    nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")
    # TODO: change this to a mock db?
    db_conn = create_connection(DATABASE)
    load_patterns(db_conn)
    return nlp, db_conn


class TestXmlParser(unittest.TestCase): 
    def SetUp(self): 
        self.nlp, self.db_conn = set_up()

    