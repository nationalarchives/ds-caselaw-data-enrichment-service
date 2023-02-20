"""Tests the `oblique_references` module"""

import sys
import unittest

sys.path.append("./")

from oblique_references.oblique_references import (
    detect_reference,
    get_replacements,
)

class TestDetectReference(unittest.TestCase):
    """Tests the `detect_reference` function"""

    def test_legislation(self):
        """
        Given a string with a ref tag with type "legislation" and an
            etype of "legislation"
        When `detect_reference` is called with these
        Then a list of tuples is returned with 1 entry
            of which the second element is the ref tag
        """
        text = 'The Act, and by that I mean <ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>, which provides as follows:'
        detected_leg = detect_reference(text, "legislation")
        assert len(detected_leg) == 1
        assert (
            detected_leg[0][1]
            == '<ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>'
        )

    def test_numbered_act(self):
        """
        Given a string referencing 1 numbered act and an etype of "act"
        When `detect_reference` is called with these
        Then a list of tuples is returned with 1 entry
            of which the second element is the reference to the numbered Act
        """
        text = 'The 1968 Act, and by that I mean <ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>, which provides as follows:'
        detected_act = detect_reference(text, "numbered_act")
        assert len(detected_act) == 1
        assert detected_act[0][1] == "The 1968 Act"

    def test_act(self):
        """
        Given a string referencing 1 act and an etype of "act"
        When `detect_reference` is called with these
        Then a list of tuples is returned with 1 entry
            of which the second element is reference to the Act
        """
        text = 'The Act, and by that I mean <ref uk:type="legislation" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19">Criminal Appeal Act 1968</ref>, which provides as follows:'
        detected_act = detect_reference(text, "act")
        assert len(detected_act) == 1
        assert detected_act[0][1] == "The Act"

    def test_multiple_acts(self):
        """
        Given a string referencing 3 acts and an etype of "act"
        When `detect_reference` is called with these
        Then a list of tuples is returned with 3 entries each
            of which has the second element references the Act
        """
        text = "This Act ... the Act ... that Act"
        detected_act = detect_reference(text, "act")
        assert len(detected_act) == 3
        assert detected_act[0][1] == "This Act"
        assert detected_act[1][1] == "the Act"
        assert detected_act[2][1] == "that Act"


class TestGetReplacements(unittest.TestCase):
    """Tests the `get_replacements` function"""

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
    ]

    def test_get_replacements(self):
        """
        Given lists of detected_acts with only unnumbered acts,
            and legislation_dicts
            and numbered_act is False
        When `get_replacements` is called with these
        Then a list of dicts containing act information is returned
            with one entry for each of the references to an act already
            defined by the time they were referenced
        """
        detected_acts = [
            ((39069, 39076), "the Act"),
            ((480464, 480472), "this Act"),
        ]
        numbered_act = False
        replacements = []

        replacements = get_replacements(
            detected_acts, self.legislation_dicts, numbered_act, replacements
        )

        expected_replacements = [
            {
                "detected_ref": "the Act",
                "ref_position": 39069,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19" uk:type="legislation" uk:origin="TNA">the Act</ref>',
            },
            {
                "detected_ref": "this Act",
                "ref_position": 480464,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1997/43" uk:canonical="1997 c. 43" uk:type="legislation" uk:origin="TNA">this Act</ref>',
            },
        ]
        assert replacements == expected_replacements

    def test_get_replacements_with_numbered_act(self):
        """
        Given lists of detected_acts with only numbered acts,
            and legislation_dicts
            and numbered_act is True
        When `get_replacements` is called with these
        Then a list of dicts containing act information is returned
            with one entry for each of the references to a numbered act
            already defined by the time they were referenced
        """
        detected_acts = [
            ((60093, 60105), "the 2000 Act"),
            ((560093, 560105), "the 2000 Act"),
        ]
        numbered_act = True
        replacements = []

        replacements = get_replacements(
            detected_acts, self.legislation_dicts, numbered_act, replacements
        )

        expected_replacements = [
            {
                "detected_ref": "the 2000 Act",
                "ref_position": 60093,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2000/6" uk:canonical="2000 c. 6" uk:type="legislation" uk:origin="TNA">the 2000 Act</ref>',
            },
            {
                "detected_ref": "the 2000 Act",
                "ref_position": 560093,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2000/6" uk:canonical="2000 c. 6" uk:type="legislation" uk:origin="TNA">the 2000 Act</ref>',
            },
        ]
        assert replacements == expected_replacements


if __name__ == "__main__":
    unittest.main()
