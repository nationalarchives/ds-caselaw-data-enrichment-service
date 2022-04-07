import unittest
import sys
sys.path.append("./")
from replacer.replacer import replacer_abbr, replacer_leg, replacer_caselaw, write_repl_file
import json

"""
    Testing the list of replacements being extracted, added to a list, 
    and confirming the format. 
"""

CITATION_REPLACEMENTS = [('[2020] EWHC 537 (Ch)', '[2020] EWHC 537 (Ch)', '2020', 'https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537', True), ('[2022] 1 P&CR 123', '[2022] 1 P&CR 123', '2022', '#', False)]
LEGISLATION_REPLACEMENTS = [('Companies Act 2006', 'http://www.legislation.gov.uk/ukpga/2006/46'), ('Trusts of Land and Appointment of Trustees Act 1996', 'https://www.legislation.gov.uk/ukpga/1996/47')]
ABBREVIATION_REPLACEMENTS = [('Dr Guy', 'Geoffrey Guy'), ('ECTHR', 'Europen Court of Human Rights')]

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
        assert replacements[0] == test_list
        test_list = ['[2022] 1 P&CR 123', '[2022] 1 P&CR 123', '2022', '#', False]
        assert replacements[1] == test_list
    
    def test_legislation(self): 
        replacements = read_file()
        test_list = ['Companies Act 2006', 'http://www.legislation.gov.uk/ukpga/2006/46']
        assert replacements[2] == test_list
        test_list = ['Trusts of Land and Appointment of Trustees Act 1996', 'https://www.legislation.gov.uk/ukpga/1996/47']
        assert replacements[3] == test_list

    def test_abbreviations(self): 
        replacements = read_file()
        test_list = ['Dr Guy', 'Geoffrey Guy']
        assert replacements[4] == test_list
        test_list = ['ECTHR', 'Europen Court of Human Rights']
        assert replacements[5] == test_list


if __name__ == '__main__':
    unittest.main()
