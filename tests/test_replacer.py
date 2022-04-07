import unittest
import sys
sys.path.append("./")
from replacer.replacer import replacer_abbr, replacer_leg, replacer_caselaw, write_repl_file

"""
    Testing the list of replacements being extracted, added to a list, 
    and confirming the format. 
"""

CITATION_REPLACEMENTS = [('[2020] EWHC 537 (Ch)', '[2020] EWHC 537 (Ch)', '2020', 'https://caselaw.nationalarchives.gov.uk/ewhc/ch/2020/537', True), ('[2022] 1 P&CR 123', '[2022] 1 P&CR 123', '2022', '#', False)]
ABBREVIATION_REPLACEMENTS = [('Dr Guy', 'Geoffrey Guy'), ('ECTHR', 'Europen Court of Human Rights')]
LEGISLATION_REPLACEMENTS = [('Companies Act 2006', 'http://www.legislation.gov.uk/ukpga/2006/46'), ('Trusts of Land and Appointment of Trustees Act 1996', 'https://www.legislation.gov.uk/ukpga/1996/47')]


"""
    This class focuses on testing the Citation Replacer and ensuring that the replacements 
    are successfully appended to the JSON file. 
"""
class TestReplacements(unittest.TestCase): 
    def set_up(self): 
        self.json = None

    def test_citation(self):
        write_repl_file("test_file.jsonl", CITATION_REPLACEMENTS)
        a = 1
        # confirm success
    
    def test_legislation(self):
        write_repl_file("test_file.jsonl", LEGISLATION_REPLACEMENTS)
        a = 1
        # confirm success
    
    def test_abbreviations(self): 
        write_repl_file("test_file.jsonl", ABBREVIATION_REPLACEMENTS)
        a = 1
        # confirm success

    
if __name__ == '__main__':
    unittest.main()
