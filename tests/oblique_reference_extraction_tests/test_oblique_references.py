import sys
import unittest

from numpy import mat

sys.path.append("./")
from bs4 import BeautifulSoup

from oblique_references.oblique_references import (
    create_legislation_dict,
    detect_reference,
    get_replacements,
)
from replacer.second_stage_replacer import oblique_replacement

"""
    This class focuses on testing the Oblique Reference detector, which identifies references to things such as 'The Act' or 'This Act'. 
"""


class TestObliqueReferencesProcessor(unittest.TestCase):
    #   self.legislation_dicts = create_legislation_dict(self.detected_leg)
    #   self.detected_numbered_acts = detect_reference(text, 'numbered_act')
    #   self.detected_acts = detect_reference(text, 'act')
    #   self.replacements = []
    #   self.replacements = get_replacements(self.detected_acts, self.legislation_dicts, False, self.replacements)
    #   self.replacements = get_replacements(self.detected_numbered_acts, self.legislation_dicts, True, self.replacements)

    def test_reference_detector(self):
        text = 'Our first piece of legislaiton is <ref canonical="2000 c. 6" href="http://www.legislation.gov.uk/id/ukpga/2000/6" type="legislation">Powers of Criminal Courts (Sentencing) Act 2000</ref>'
        detected_leg = detect_reference(text, "legislation")
        # 6 pieces of legislation in the test file
        assert len(detected_leg) == 1
        assert (
            detected_leg[0][1]
            == '<ref canonical="2000 c. 6" href="http://www.legislation.gov.uk/id/ukpga/2000/6" type="legislation">Powers of Criminal Courts (Sentencing) Act 2000</ref>'
        )

        text = 'The Act, and by that I mean <ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>, which provides as follows:'
        detected_leg = detect_reference(text, "legislation")
        # 6 pieces of legislation in the test file
        assert len(detected_leg) == 1
        assert (
            detected_leg[0][1]
            == '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>'
        )

        text = 'The Act, and by that I mean <ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>, which provides as follows:'
        detected_act = detect_reference(text, "act")
        assert len(detected_act) == 1
        assert detected_act[0][1] == "The Act"

        text = "This Act ... the Act ... that Act"
        detected_act = detect_reference(text, "act")
        assert len(detected_act) == 3
        assert detected_act[0][1] == "This Act"
        assert detected_act[1][1] == "the Act"
        assert detected_act[2][1] == "that Act"

    # testing the matching of the replacements
    def test_get_replacements(self):
        detected_acts = [((33958, 33966), "this Act")]
        legislation_dicts = [
            {
                "pos": (4670, 4814),
                "detected_leg": "Homicide Act 1957",
                "href": "http://www.legislation.gov.uk/id/ukpga/Eliz2/5-6/11",
                "canonical": "1957 (5  6 Eliz. 2) c. 11",
                "year": "1957",
            },
            {
                "pos": (33697, 33828),
                "detected_leg": "Criminal Appeal Act 1968",
                "href": "http://www.legislation.gov.uk/id/ukpga/1968/19",
                "canonical": "1968 c. 19",
                "year": "1968",
            },
            {
                "pos": (54039, 54191),
                "detected_leg": "Powers of Criminal Courts (Sentencing) Act 2000",
                "href": "http://www.legislation.gov.uk/id/ukpga/2000/6",
                "canonical": "2000 c. 6",
                "year": "2000",
            },
            {
                "pos": (58974, 59106),
                "detected_leg": "Criminal Justice Act 1991",
                "href": "http://www.legislation.gov.uk/id/ukpga/1991/53",
                "canonical": "1991 c. 53",
                "year": "1991",
            },
            {
                "pos": (61932, 62065),
                "detected_leg": "Crime (Sentences) Act 1997",
                "href": "http://www.legislation.gov.uk/id/ukpga/1997/43",
                "canonical": "1997 c. 43",
                "year": "1997",
            },
            {
                "pos": (62100, 62252),
                "detected_leg": "Powers of Criminal Courts (Sentencing) Act 2000",
                "href": "http://www.legislation.gov.uk/id/ukpga/2000/6",
                "canonical": "2000 c. 6",
                "year": "2000",
            },
        ]
        numbered_Act = False
        replacements = []
        replacements = get_replacements(
            detected_acts, legislation_dicts, numbered_Act, replacements
        )
        ex_replacements = [
            {
                "detected_ref": "this Act",
                "ref_position": 33958,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19" uk:type="legislation">this Act</ref>',
            }
        ]

        assert replacements == ex_replacements

        detected_acts = [
            ((10093, 10105), "the 1985 Act"),
            ((37166, 37178), "the 1985 Act"),
        ]
        legislation_dicts = [
            {
                "pos": (8811, 8934),
                "detected_leg": "Housing Act 1985",
                "href": "http://www.legislation.gov.uk/id/ukpga/1985/68",
                "canonical": "1985 c. 68",
                "year": "1985",
            },
            {
                "pos": (26808, 26943),
                "detected_leg": "Landlord and Tenant Act 1985",
                "href": "http://www.legislation.gov.uk/id/ukpga/1985/70",
                "canonical": "1985 c. 70",
                "year": "1985",
            },
            {
                "pos": (46079, 46202),
                "detected_leg": "Finance Act 1972",
                "href": "http://www.legislation.gov.uk/id/ukpga/1972/41",
                "canonical": "1972 c. 41",
                "year": "1972",
            },
            {
                "pos": (46220, 46343),
                "detected_leg": "Housing Act 1974",
                "href": "http://www.legislation.gov.uk/id/ukpga/1974/44",
                "canonical": "1974 c. 44",
                "year": "1974",
            },
            {
                "pos": (46371, 46494),
                "detected_leg": "Housing Act 1980",
                "href": "http://www.legislation.gov.uk/id/ukpga/1980/51",
                "canonical": "1980 c. 51",
                "year": "1980",
            },
            {
                "pos": (48329, 48464),
                "detected_leg": "Landlord and Tenant Act 1985",
                "href": "http://www.legislation.gov.uk/id/ukpga/1985/70",
                "canonical": "1985 c. 70",
                "year": "1985",
            },
            {
                "pos": (53463, 53598),
                "detected_leg": "Landlord and Tenant Act 1985",
                "href": "http://www.legislation.gov.uk/id/ukpga/1985/70",
                "canonical": "1985 c. 70",
                "year": "1985",
            },
        ]
        numbered_Act = True
        replacements = []
        replacements = get_replacements(
            detected_acts, legislation_dicts, numbered_Act, replacements
        )
        ex_replacements = [
            {
                "detected_ref": "the 1985 Act",
                "ref_position": 10093,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1985/68" uk:canonical="1985 c. 68" uk:type="legislation">the 1985 Act</ref>',
            },
            {
                "detected_ref": "the 1985 Act",
                "ref_position": 37166,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1985/68" uk:canonical="1985 c. 68" uk:type="legislation">the 1985 Act</ref>',
            },
        ]
        assert replacements == ex_replacements

        detected_acts = [((39069, 39076), "the Act"), ((480464, 480472), "this Act")]
        legislation_dicts = [
            {
                "pos": (37538, 37661),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (38061, 38184),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (38823, 38946),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (41474, 41597),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (41698, 41821),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (41899, 42022),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (44121, 44244),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (44746, 44869),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (69394, 69517),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (375110, 375233),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (479857, 479980),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (480695, 480818),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (485449, 485572),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (488035, 488158),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (512563, 512686),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (524500, 524623),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (529535, 529658),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
            {
                "pos": (541342, 541465),
                "detected_leg": "Patents Act 1977",
                "href": "http://www.legislation.gov.uk/id/ukpga/1977/37",
                "canonical": "1977 c. 37",
                "year": "1977",
            },
        ]
        numbered_Act = False
        replacements = []
        replacements = get_replacements(
            detected_acts, legislation_dicts, numbered_Act, replacements
        )
        ex_replacements = [
            {
                "detected_ref": "the Act",
                "ref_position": 39069,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1977/37" uk:canonical="1977 c. 37" uk:type="legislation">the Act</ref>',
            },
            {
                "detected_ref": "this Act",
                "ref_position": 480464,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1977/37" uk:canonical="1977 c. 37" uk:type="legislation">this Act</ref>',
            },
        ]
        assert replacements == ex_replacements


if __name__ == "__main__":
    unittest.main()
