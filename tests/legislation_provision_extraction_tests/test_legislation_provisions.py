import unittest
from numpy import mat
import sys
sys.path.append("./")
from replacer.second_stage_replacer import provision_replacement
from legislation_provisions_extraction.legislation_provisions import detect_reference, find_closest_legislation, get_clean_section_number, save_section_to_dict

correct_references = ["section 23 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref>, which provides as follows:", 
    "Section 129 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>", 
    "section 23 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref> and Section 129 of the \
         <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>"]


"""
    This class focuses on testing the Legislation Provision processor, which detects references to sections and links them to the 
    section within the legislation itself. 
"""
class TestLegislationProvisionProcessor(unittest.TestCase): 
    # Handling extra characters around the citations to ensure that spacy handles it well
    def test_leg_detect_reference(self): 

        ref = "section 23 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref>, which provides as follows:"
        leg_ref = detect_reference(ref)
        assert leg_ref[0][1] == "<ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref>"

        ref = "Section 129 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>"
        leg_ref = detect_reference(ref)
        assert leg_ref[0][1] == "<ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>"

        # handle multiple legislation in one sentence
        ref = "section 23 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref> and Section 129 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>"
        leg_ref = detect_reference(ref)
        assert leg_ref[0][1] == "<ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref>"
        assert leg_ref[1][1] == "<ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>"
    
    def test_section_detect_reference(self): 
        ref = "section 23 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1968/19\" uk:canonical=\"1968 c. 19\">Criminal Appeal Act 1968</ref>, which provides as follows:"
        sec_ref = detect_reference(ref, 'section')
        assert sec_ref[0][1] == "section 23"

        ref = "Section 129 of the <ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>"
        sec_ref = detect_reference(ref, 'section')
        assert sec_ref[0][1] == "Section 129"

    def test_find_closest_leg(self): 
        # section 130 should be out of the threshold for the Patents Act 1977
        sec = [((129, 142), 'Section 67(1)'), ((7052, 7066), 'section 130')]
        leg = [((150, 273), '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">Patents Act 1977</ref>')]
        sec_to_leg = find_closest_legislation(sec, leg)

        assert sec_to_leg[0][1] == "Section 67(1)"
        # assert section 130 not found as being close to the legislation
        assert len(sec_to_leg) == 1 

        sec = [((129, 142), 'Section 67(1)'), ((752, 766), 'section 130')]
        leg = [((150, 273), '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">Patents Act 1977</ref>'), ((740, 742), '<ref uk:type=\"legislation\" href=\"http://www.legislation.gov.uk/id/ukpga/1985/68\" uk:canonical=\"1985 c. 68\">Housing Act 1985</ref>')]
        sec_to_leg = find_closest_legislation(sec, leg)

        assert sec_to_leg[0][0] == "<ref canonical=\"1977 c. 37\" href=\"http://www.legislation.gov.uk/id/ukpga/1977/37\" type=\"legislation\">Patents Act 1977</ref>"
        assert sec_to_leg[0][1] == "Section 67(1)"

        assert sec_to_leg[1][1] == "section 130"
    
    def test_clean_sec_number(self):
        sec = "Section 67(1)"
        clean_sec = get_clean_section_number(sec)

        assert clean_sec == "67"

        sec = "Section 140.2(1)(A)"
        clean_sec = get_clean_section_number(sec)

        assert clean_sec == "140"
    
     

if __name__ == '__main__':
    unittest.main()
