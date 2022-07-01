import unittest
from numpy import mat
import sys
sys.path.append("./")
from replacer.second_stage_replacer import provision_replacement
from legislation_provisions_extraction.legislation_provisions import detect_reference, find_closest_legislation, get_clean_section_number, provision_resolver


"""
    This class focuses on testing the Legislation Provision processor, which detects references to sections and links them to the 
    section within the legislation itself. 
"""
class TestLegislationProvisionProcessor(unittest.TestCase): 

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
    
    def test_resolver_single_match(self):
        section_dict = {'section 55': [{'para_number': 115, 'section_position': 276, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/55', 'section_canonical': '1906 (6 Edw. 7) c. 41 s. 55', 'ref': '<ref canonical="1906 (6 Edw. 7) c. 41" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41" type="legislation">Marine Insurance Act 1906</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41', 'canonical': '1906 (6 Edw. 7) c. 41'}, {'para_number': 937, 'section_position': 1066, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/55', 'section_canonical': '1906 (6 Edw. 7) c. 41 s. 55', 'ref': '<ref canonical="1906 (6 Edw. 7) c. 41" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41" type="legislation">Marine Insurance Act 1906</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41', 'canonical': '1906 (6 Edw. 7) c. 41'}], 'section 41': [{'para_number': 991, 'section_position': 182, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/41', 'section_canonical': '1906 (6 Edw. 7) c. 41 s. 41', 'ref': '<ref canonical="1906 (6 Edw. 7) c. 41" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41" type="legislation">Marine Insurance Act 1906</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41', 'canonical': '1906 (6 Edw. 7) c. 41', 'section_ref': '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/41" uk:canonical="1906 (6 Edw. 7) c. 41 s. 41">section 41</ref>'}], 'section 3': [{'para_number': 991, 'section_position': 376, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/3', 'section_canonical': '1906 (6 Edw. 7) c. 41 s. 3', 'ref': '<ref canonical="1906 (6 Edw. 7) c. 41" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41" type="legislation">the Act</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/Edw7/6/41', 'canonical': '1906 (6 Edw. 7) c. 41', 'section_ref': '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/3" uk:canonical="1906 (6 Edw. 7) c. 41 s. 3">Section 3</ref>'}]}
        match = [((170, 180), 'section 41')]
        para_number = 1005
        ex_resolved_ref = [{'detected_ref': 'section 41', 'ref_para': 1005, 'ref_position': 170, 'ref_tag': '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/Edw7/6/41/section/41" uk:canonical="1906 (6 Edw. 7) c. 41 s. 41">section 41</ref>'}]
        resolved_ref = provision_resolver(section_dict, match, para_number)

        assert ex_resolved_ref == resolved_ref

        section_dict = {'section 1': [{'para_number': 202, 'section_position': 950, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37/section/1', 'section_canonical': '1977 c. 37 s. 1', 'ref': '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">Patents Act 1977</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37', 'canonical': '1977 c. 37'}]}
        match = [((950, 962), 'Section 1(1)')]
        para_number = 202
        ex_resolved_ref = [{'detected_ref': 'Section 1(1)', 'ref_para': 202, 'ref_position': 950, 'ref_tag': '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1977/37/section/1/1" uk:canonical="1977 c. 37 s. 1">Section 1(1)</ref>'}]
        resolved_ref = provision_resolver(section_dict, match, para_number)

        assert ex_resolved_ref == resolved_ref

    def test_multiple_matches_resolver(self):
        section_dict = {'section 1': [{'para_number': 202, 'section_position': 950, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37/section/1', 'section_canonical': '1977 c. 37 s. 1', 'ref': '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">Patents Act 1977</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37', 'canonical': '1977 c. 37'}, {'para_number': 203, 'section_position': 349, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37/section/1', 'section_canonical': '1977 c. 37 s. 1', 'ref': '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">Patents Act 1977</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37', 'canonical': '1977 c. 37'}], 'section 2': [{'para_number': 205, 'section_position': 404, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37/section/2', 'section_canonical': '1977 c. 37 s. 2', 'ref': '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">Patents Act 1977</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37', 'canonical': '1977 c. 37'}, {'para_number': 205, 'section_position': 654, 'section_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37/section/2', 'section_canonical': '1977 c. 37 s. 2', 'ref': '<ref canonical="1977 c. 37" href="http://www.legislation.gov.uk/id/ukpga/1977/37" type="legislation">the Act</ref>', 'leg_href': 'http://www.legislation.gov.uk/id/ukpga/1977/37', 'canonical': '1977 c. 37'}]}
        match = [((404, 416), 'Section 2(1)'), ((654, 666), 'Section 2(2)')]
        para_number = 205
        ex_resolved_ref = [{'detected_ref': 'Section 2(1)', 'ref_para': 205, 'ref_position': 404, 'ref_tag': '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1977/37/section/2/1" uk:canonical="1977 c. 37 s. 2">Section 2(1)</ref>'}, {'detected_ref': 'Section 2(2)', 'ref_para': 205, 'ref_position': 654, 'ref_tag': '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1977/37/section/2/2" uk:canonical="1977 c. 37 s. 2">Section 2(2)</ref>'}]
        resolved_ref = provision_resolver(section_dict, match, para_number)

        assert ex_resolved_ref == resolved_ref

if __name__ == '__main__':
    unittest.main()
