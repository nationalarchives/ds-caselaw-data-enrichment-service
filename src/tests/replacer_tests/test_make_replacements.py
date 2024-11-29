from pathlib import Path

import pytest

from replacer.make_replacments import (
    _remove_old_enrichment_references,
    make_post_header_replacements,
    split_text_by_closing_header_tag,
)
from utils.compare_xml import assert_equal_xml

FIXTURE_DIR = Path(__file__).parent.parent.resolve() / "fixtures/"


class TestMakePostHeaderReplacements:
    def test_make_post_header_replacements(self):
        original_file_content = open(FIXTURE_DIR / "ewhc-ch-2023-257_original.xml", encoding="utf-8").read()
        replacement_content = open(FIXTURE_DIR / "ewhc-ch-2023-257_replacements.txt", encoding="utf-8").read()
        expected_file_content = open(
            FIXTURE_DIR / "ewhc-ch-2023-257_enriched_stage_1.xml",
            encoding="utf-8",
        ).read()

        content_with_replacements = make_post_header_replacements(original_file_content, replacement_content)
        assert_equal_xml(content_with_replacements, expected_file_content)

    def test_post_header_works_if_already_enriched(self):
        original_file_content = open(
            FIXTURE_DIR / "ewhc-ch-2023-257_enriched_stage_1.xml",
            encoding="utf-8",
        ).read()
        replacement_content = open(FIXTURE_DIR / "ewhc-ch-2023-257_replacements.txt", encoding="utf-8").read()
        expected_file_content = open(
            FIXTURE_DIR / "ewhc-ch-2023-257_enriched_stage_1.xml",
            encoding="utf-8",
        ).read()

        content_with_replacements = make_post_header_replacements(original_file_content, replacement_content)

        assert_equal_xml(content_with_replacements, expected_file_content)

    def test_post_header_double_replacement(self):
        """When a value is replaced, the value is an attribute in a ref tag.
        If the replacement value is then replaced, invalid XML was generated."""

        original_file_content = """<?xml version="1.0" encoding="utf-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:html="http://www.w3.org/1999/xhtml" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
<judgment name="judgment">
<header></header><judgmentBody>a</judgmentBody></judgment></akomaNtoso>
"""

        replacement_content = """
        {"case": ["a", "b", "2008", "#", true]}
        {"case": ["b", "c", "1937", "#", true]}
        """.strip()
        expected_file_content = """<?xml version="1.0" encoding="utf-8"?>
        <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:html="http://www.w3.org/1999/xhtml" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
        <judgment name="judgment"><header/><judgmentBody>
        <ref xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="b" uk:year="2008" uk:origin="TNA">a</ref>
        </judgmentBody></judgment></akomaNtoso>"""
        content_with_replacements = make_post_header_replacements(original_file_content, replacement_content)
        assert_equal_xml(content_with_replacements, expected_file_content)

    def test_remove_nested_legislation_references(self):
        tidy_output = _remove_old_enrichment_references(
            """
            <xml xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0' xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <a><e><ref uk:origin="TNA"><ref uk:origin="TNA"><b>AAA</b></ref><c/></ref>D</e></a>
            </xml>""",
        )

        assert "<a><e><b>AAA</b><c/>D</e></a>" in tidy_output

    def test_dont_delete_not_TNA_ref_tags(self):
        assert "not-TNA" in _remove_old_enrichment_references(
            """<xml xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0' xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <ref uk:origin="not-TNA"></ref>
            </xml>""",
        )

    def test_delete_no_origin_ref_tags(self):
        assert "ref" not in _remove_old_enrichment_references(
            """<xml xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0' xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <ref></ref>
            </xml>""",
        )


class TestSplitTextByClosingHeaderTag:
    @pytest.mark.parametrize("closing_header_tag", ["</header>", "<header/>"])
    def test_split_text_by_closing_header_tag(self, closing_header_tag):
        file_content = f"ABC{closing_header_tag}DEF"
        assert split_text_by_closing_header_tag(file_content) == (
            "ABC",
            closing_header_tag,
            "DEF",
        )

    @pytest.mark.parametrize("invalid_closing_header_tag", ["</foo>", "<foo/>"])
    def test_no_split(self, invalid_closing_header_tag):
        file_content = f"ABC{invalid_closing_header_tag}DEF"
        assert split_text_by_closing_header_tag(file_content) == ("", "", file_content)
