"""Unit Tests for the `second_stage_replacer` module"""

import unittest

from bs4 import BeautifulSoup

from replacer.second_stage_replacer import replace_references_by_paragraph


class TestSecondStageReplacer(unittest.TestCase):
    def test_replace_references_by_paragraph(self):
        """
        Given some file_data soup and references with ref_tag and positional info
        When `replace_references_by_paragraph` is called with these
        Then an enriched string is returned with the references replaced by the
            corresponding ref tag
        """
        input_file_path = "tests/fixtures/ewhc-ch-2023-257_enriched_stage_1.xml"
        with open(input_file_path, "r", encoding="utf-8") as input_file:
            file_content = input_file.read()
        file_data = BeautifulSoup(file_content, "xml")

        references = [
            {
                "detected_ref": "that Act",
                "ref_para": 153,
                "ref_position": 186,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1996/14" uk:canonical="1996 c. 14" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "that Act",
                "ref_para": 154,
                "ref_position": 214,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/1996/14" uk:canonical="1996 c. 14" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "that Act",
                "ref_para": 159,
                "ref_position": 387,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2020/7" uk:canonical="2020 c. 7" uk:type="legislation" uk:origin="TNA">that Act</ref>',
            },
            {
                "detected_ref": "the 2004 Act",
                "ref_para": 100,
                "ref_position": 487,
                "ref_tag": '<ref href="http://www.legislation.gov.uk/id/ukpga/2004/12" uk:canonical="2004 c. 12" uk:type="legislation" uk:origin="TNA">the 2004 Act</ref>',
            },
        ]

        enriched_content = replace_references_by_paragraph(file_data, references)

        expected_file_path = "tests/fixtures/ewhc-ch-2023-257_enriched_stage_2.xml"
        with open(expected_file_path, "r", encoding="utf-8") as expected_file:
            expected_enriched_content = expected_file.read()

        assert enriched_content == expected_enriched_content


if __name__ == "__main__":
    unittest.main()
