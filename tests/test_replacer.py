import unittest
import sys
sys.path.append("./")
from replacer.replacer import write_repl_file
import json
from collections import namedtuple

case = namedtuple('case', 'citation_match corrected_citation year URI is_neutral')
abb = namedtuple('abb', 'abb_match longform')
leg = namedtuple('leg', 'detected_ref href')

"""
    Testing the list of replacements being extracted, added to a list, 
    and confirming the format. 
"""


CITATION_REPLACEMENTS = [case(citation_match='[2020] EWHC 537 (Ch)', corrected_citation='[2020] EWHC 537 (Ch)', year='2020', URI='https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537', is_neutral=True), case(citation_match='[2022] 1 P&CR 123', corrected_citation='[2022] 1 P&CR 123', year='2022',URI= '#', is_neutral=False)]
LEGISLATION_REPLACEMENTS = [leg(detected_ref='Companies Act 2006', href='http://www.legislation.gov.uk/ukpga/2006/46'), leg(detected_ref='Trusts of Land and Appointment of Trustees Act 1996', href='https://www.legislation.gov.uk/ukpga/1996/47')]
ABBREVIATION_REPLACEMENTS = [abb(abb_match='Dr Guy', longform='Geoffrey Guy'), abb(abb_match='ECTHR', longform='Europen Court of Human Rights')]

def read_file(): 
    replacements = []
    tuple_file = open("tuples.jsonl", "r")
    for line in tuple_file:
        replacements.append(json.loads(line))
    tuple_file.close()
    return replacements

"""
    This class focuses on testing the Citation Replacer and ensuring that the replacements 
    are successfully appended to the JSON file. 
"""
class TestReplacements(unittest.TestCase): 
    def test_write_file(self):
        tuple_file = open("tuples.jsonl", "w+")
        write_repl_file(tuple_file, CITATION_REPLACEMENTS)
        write_repl_file(tuple_file, LEGISLATION_REPLACEMENTS)
        write_repl_file(tuple_file, ABBREVIATION_REPLACEMENTS)
        tuple_file.close()

    def test_citations(self): 
        replacements = read_file()
        test_list = ['[2020] EWHC 537 (Ch)', '[2020] EWHC 537 (Ch)', '2020', 'https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537', True]
        key, value = list(replacements[0].items())[0]
        assert key == "case"
        assert value == test_list
        test_list = ['[2022] 1 P&CR 123', '[2022] 1 P&CR 123', '2022', '#', False]
        key, value = list(replacements[1].items())[0]
        assert key == "case"
        assert value == test_list
    
    def test_legislation(self): 
        replacements = read_file()
        test_list = ['Companies Act 2006', 'http://www.legislation.gov.uk/ukpga/2006/46']
        key, value = list(replacements[2].items())[0]
        assert key == "leg"
        assert value == test_list
        test_list = ['Trusts of Land and Appointment of Trustees Act 1996', 'https://www.legislation.gov.uk/ukpga/1996/47']
        key, value = list(replacements[3].items())[0]
        assert key == "leg"
        assert value == test_list

    def test_abbreviations(self): 
        replacements = read_file()
        test_list = ['Dr Guy', 'Geoffrey Guy']
        key, value = list(replacements[4].items())[0]
        assert key == "abb"
        assert value == test_list
        test_list = ['ECTHR', 'Europen Court of Human Rights']
        key, value = list(replacements[5].items())[0]
        assert key == "abb"
        assert value == test_list

if __name__ == '__main__':
    unittest.main()
