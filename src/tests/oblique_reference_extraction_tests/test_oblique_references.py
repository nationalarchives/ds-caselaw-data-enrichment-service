"""Tests the `oblique_references` module"""


import re
import unittest
from pathlib import Path
from typing import Dict, List, Union

import pytest
from caselawclient.content_hash import get_hash_from_document

from oblique_references.enrich_oblique_references import (
    enrich_oblique_references,
)
from oblique_references.oblique_references import (
    LegislationReferenceReplacements,
    NotExactlyOneRefTag,
    create_legislation_dict,
    detect_reference,
    get_oblique_reference_replacements_by_paragraph,
    get_replacements,
)
from replacer.second_stage_replacer import replace_references

FIXTURE_DIR = Path(__file__).parent.parent.resolve() / "fixtures/"


def nuke_tags(xml):
    return "".join(re.findall(">([^<]*)<", str(xml)))


class TestOutputHasSameHashAsInput(unittest.TestCase):
    def test_rwanda_overall(self):
        input_file_path = f"{FIXTURE_DIR}/rwanda.xml"
        with open(input_file_path, "rb") as input_file:
            input_file_content = input_file.read()
        output = enrich_oblique_references(input_file_content).encode("utf-8")
        in_hash = get_hash_from_document(input_file_content)
        out_hash = get_hash_from_document(output)
        assert in_hash == out_hash

    def test_rwanda_specific(self):
        text = '<p class="ParaApprovedLevel1" style="margin-left:0in;text-indent:0.5in"><span style="font-family:\'Times New Roman\'">Thirdly, section 82(1) of the <ref href="http://www.legislation.gov.uk/id/ukpga/2002/41" uk:canonical="2002 c. 41" uk:origin="TNA" uk:type="legislation">Nationality, Immigration and Asylum Act 2002</ref> (“the 2002 Act”), read together with section 84(1) of that Act, confers a right of appeal against the refusal of a protection claim (defined by section 82(2) as including a claim that the removal of a person from the United Kingdom would breach the United Kingdom’s obligations under the Refugee Convention) on the ground that removal of the person from the United Kingdom would breach the United Kingdom’s obligations under that Convention. Section 82(1), read together with section 84(2), also confers a right of appeal against the refusal of a human rights claim (defined by section 113(1) as a claim that to remove the person from the United Kingdom would be unlawful under the Human Rights Act) on the ground that removal of the person from the United Kingdom would be unlawful under section 6 of that Act. The principle of non-refoulement is therefore given effect by sections 82 and 84 of the 2002 Act, both as it is set out in the Refugee Convention and as it applies under the Human Rights Act. </span></p>'
        reference_replacements = [
            {
                "detected_ref": "that Act",
                "ref_position": 374,
                "ref_para": 64,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2002/41" uk:canonical="2002 c. 41" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "that Act",
                "ref_position": 1122,
                "ref_para": 64,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2002/41" uk:canonical="2002 c. 41" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "the 2002 Act",
                "ref_position": 322,
                "ref_para": 64,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2002/41" uk:canonical="2002 c. 41" uk:type="legislation" uk:origin="TNA">the 2002 Act</ref>',
            },
            {
                "detected_ref": "the 2002 Act",
                "ref_position": 1216,
                "ref_para": 64,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2002/41" uk:canonical="2002 c. 41" uk:type="legislation" uk:origin="TNA">the 2002 Act</ref>',
            },
        ]
        assert nuke_tags(replace_references(text, reference_replacements)) == nuke_tags(
            text
        )


class TestGetObliqueReferenceReplacementsByParagraph(unittest.TestCase):
    """Tests the `get_oblique_reference_replacements_by_paragraph` function"""

    def test_get_oblique_reference_replacements_by_paragraph(self):
        """
        Given xml judgment content without enriched oblique references
        When it is passed to `get_oblique_reference_replacements_by_paragraph`
        Then a dict of replacement information for each oblique detected reference
            is returned
        """
        input_file_path = f"{FIXTURE_DIR}/ewhc-ch-2023-257_enriched_stage_1.xml"
        with open(input_file_path, "r", encoding="utf-8") as input_file:
            input_file_content = input_file.read()
        oblique_reference_replacements = (
            get_oblique_reference_replacements_by_paragraph(input_file_content)
        )
        assert oblique_reference_replacements == [
            {
                "detected_ref": "the 2004 Act",
                "ref_position": 487,
                "ref_para": 100,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:type="legislation" uk:origin="TNA">the 2004 Act</ref>',
            },
            {
                "detected_ref": "that Act",
                "ref_position": 186,
                "ref_para": 153,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/1996/14" uk:canonical="1996 c. 14" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "that Act",
                "ref_position": 214,
                "ref_para": 154,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/1996/14" uk:canonical="1996 c. 14" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "that Act",
                "ref_position": 387,
                "ref_para": 159,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/2020/7" uk:canonical="2020 c. 7" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
        ]


class TestCreateLegislationDict(unittest.TestCase):
    """Tests the `create_legislation_dict` function"""

    def test_create_legislation_dict(self):
        """
        Given a list of detected_legislations
        And a paragraph number for which paragraph they were built from
        When they are passed to `create_legislation_dict`
        Then a list of LegislationDicts is created with information for each oblique
            detected reference is returned
        """
        detected_legislation = [
            (
                (307, 452),
                '<ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation">Finance Act 2004</ref>',
            ),
            (
                (588, 733),
                '<ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">Finance Act 2004</ref>',
            ),
        ]
        paragraph_number = 2
        oblique_reference_replacements = create_legislation_dict(
            detected_legislation, paragraph_number
        )
        assert oblique_reference_replacements == [
            {
                "para": 2,
                "para_pos": (307, 452),
                "detected_leg": "Finance Act 2004",
                "href": "http://www.legislation.gov.uk/id/ukpga/2004/12",
                "canonical": "2004 c. 12",
                "year": "2004",
            },
            {
                "para": 2,
                "para_pos": (588, 733),
                "detected_leg": "Finance Act 2004",
                "href": "http://www.legislation.gov.uk/id/ukpga/2004/12",
                "canonical": "2004 c. 12",
                "year": "2004",
            },
        ]

    def test_bad_year_info(self):
        """
        Given a list of detected_legislations that do not have a year in their texts
        And a paragraph number for which paragraph they were built from
        When they are passed to `create_legislation_dict`
        Then a list of LegislationDicts is created with information for each oblique
            detected reference is returned with empty `year` information
        """
        detected_legislation = [
            (
                (307, 451),
                '<ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation">Finance Act 200</ref>',
            ),
            (
                (507, 636),
                '<ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation"></ref>',
            ),
            (
                (707, 847),
                '<ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation">Finance Act</ref>',
            ),
        ]
        paragraph_number = 2
        oblique_reference_replacements = create_legislation_dict(
            detected_legislation, paragraph_number
        )
        assert oblique_reference_replacements == [
            {
                "para": 2,
                "para_pos": (307, 451),
                "detected_leg": "Finance Act 200",
                "href": "http://www.legislation.gov.uk/id/ukpga/2004/12",
                "canonical": "2004 c. 12",
                "year": "",
            },
            {
                "para": 2,
                "para_pos": (507, 636),
                "detected_leg": "",
                "href": "http://www.legislation.gov.uk/id/ukpga/2004/12",
                "canonical": "2004 c. 12",
                "year": "",
            },
            {
                "para": 2,
                "para_pos": (707, 847),
                "detected_leg": "Finance Act",
                "href": "http://www.legislation.gov.uk/id/ukpga/2004/12",
                "canonical": "2004 c. 12",
                "year": "",
            },
        ]

    def test_malformed_refs(self):
        """
        Given a list of detected_legislation dicts with malformed refs
        And a paragraph number for which paragraph they were built from
        When they are passed to `create_legislation_dict`
        Then a list of LegislationDicts is created with information for each oblique detected reference
            is returned with empty `year` information
        """
        detected_legislation = [
            (
                (307, 452),
                '<bad_ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation">Finance Act 2004</bad_ref>',
            ),
            (
                (588, 733),
                '<ref bad_href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:bad_canonical="2004 c. 12" uk:origin="TNA" uk:type="legislation">Finance Act 2004</bad_ref>',
            ),
        ]
        paragraph_number = 2
        with pytest.raises(NotExactlyOneRefTag):
            create_legislation_dict(detected_legislation, paragraph_number)


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
            "para_pos": (4670, 4814),
            "para": 1,
            "detected_leg": "Homicide Act 1957",
            "href": "http://www.legislation.gov.uk/id/ukpga/Eliz2/5-6/11",
            "canonical": "1957 (5  6 Eliz. 2) c. 11",
            "year": "1957",
        },
        {
            "para_pos": (33697, 33828),
            "para": 1,
            "detected_leg": "Criminal Appeal Act 1968",
            "href": "http://www.legislation.gov.uk/id/ukpga/1968/19",
            "canonical": "1968 c. 19",
            "year": "1968",
        },
        {
            "para_pos": (54039, 54191),
            "para": 1,
            "detected_leg": "Powers of Criminal Courts (Sentencing) Act 2000",
            "href": "http://www.legislation.gov.uk/id/ukpga/2000/6",
            "canonical": "2000 c. 6",
            "year": "2000",
        },
        {
            "para_pos": (58974, 59106),
            "para": 1,
            "detected_leg": "Criminal Justice Act 1991",
            "href": "http://www.legislation.gov.uk/id/ukpga/1991/53",
            "canonical": "1991 c. 53",
            "year": "1991",
        },
        {
            "para_pos": (61932, 62065),
            "para": 1,
            "detected_leg": "Crime (Sentences) Act 1997",
            "href": "http://www.legislation.gov.uk/id/ukpga/1997/43",
            "canonical": "1997 c. 43",
            "year": "1997",
        },
        {
            "para_pos": (4670, 4814),
            "para": 2,
            "detected_leg": "Homicide Act 1957",
            "href": "http://www.legislation.gov.uk/id/ukpga/Eliz2/5-6/11",
            "canonical": "1957 (5  6 Eliz. 2) c. 11",
            "year": "1957",
        },
        {
            "para_pos": (33697, 33828),
            "para": 2,
            "detected_leg": "Criminal Appeal Act 1968",
            "href": "http://www.legislation.gov.uk/id/ukpga/1968/19",
            "canonical": "1968 c. 19",
            "year": "1968",
        },
        {
            "para_pos": (54039, 54191),
            "para": 2,
            "detected_leg": "Powers of Criminal Courts (Sentencing) Act 2000",
            "href": "http://www.legislation.gov.uk/id/ukpga/2000/6",
            "canonical": "2000 c. 6",
            "year": "2000",
        },
        {
            "para_pos": (58974, 59106),
            "para": 2,
            "detected_leg": "Criminal Justice Act 1991",
            "href": "http://www.legislation.gov.uk/id/ukpga/1991/53",
            "canonical": "1991 c. 53",
            "year": "1991",
        },
        {
            "para_pos": (61932, 62065),
            "para": 2,
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
            and a paragraph_number
        When `get_replacements` is called with these
        Then a list of dicts containing act information is returned
            with one entry for each of the references to an act already
            defined by the time they were referenced in that paragraph
        """
        detected_acts = [
            ((39069, 39076), "the Act"),
            ((480464, 480472), "this Act"),
        ]
        numbered_act = False
        replacements: LegislationReferenceReplacements = []

        paragraph_number = 2

        replacements = get_replacements(
            detected_acts,
            self.legislation_dicts,
            numbered_act,
            replacements,
            paragraph_number,
        )

        expected_replacements = [
            {
                "detected_ref": "the Act",
                "ref_position": 39069,
                "ref_para": 2,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/1968/19" uk:canonical="1968 c. 19" uk:type="legislation" uk:origin="TNA">the Act</ref>',
            },
            {
                "detected_ref": "this Act",
                "ref_position": 480464,
                "ref_para": 2,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/1997/43" uk:canonical="1997 c. 43" uk:type="legislation" uk:origin="TNA">this Act</ref>',
            },
        ]
        assert replacements == expected_replacements

    def test_get_replacements_with_numbered_act(self):
        """
        Given lists of detected_acts with only numbered acts,
            and legislation_dicts
            and numbered_act is True
            and a paragraph_number
        When `get_replacements` is called with these
        Then a list of dicts containing act information is returned
            with one entry for each of the references to a numbered act
            already defined by the time they were referenced in that paragraph
        """
        detected_acts = [
            ((60093, 60105), "the 2000 Act"),
            ((560093, 560105), "the 2000 Act"),
        ]
        numbered_act = True
        replacements: List[Dict[str, Union[str, int]]] = []

        paragraph_number = 2

        replacements = get_replacements(
            detected_acts,
            self.legislation_dicts,
            numbered_act,
            replacements,
            paragraph_number,
        )

        expected_replacements = [
            {
                "detected_ref": "the 2000 Act",
                "ref_position": 60093,
                "ref_para": 2,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/2000/6" uk:canonical="2000 c. 6" uk:type="legislation" uk:origin="TNA">the 2000 Act</ref>',
            },
            {
                "detected_ref": "the 2000 Act",
                "ref_position": 560093,
                "ref_para": 2,
                "ref_tag": '<ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" href="http://www.legislation.gov.uk/id/ukpga/2000/6" uk:canonical="2000 c. 6" uk:type="legislation" uk:origin="TNA">the 2000 Act</ref>',
            },
        ]
        assert replacements == expected_replacements


if __name__ == "__main__":
    unittest.main()
