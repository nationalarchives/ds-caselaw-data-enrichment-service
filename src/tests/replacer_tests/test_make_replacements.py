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
    def test_make_failing_post_header_replacements(self):
        """This used to fail because the input data contained ref tags with text matching a replacement"""
        original_file_content = open(FIXTURE_DIR / "broken.xml", encoding="utf-8").read()
        replacement_content = open(FIXTURE_DIR / "broken.txt", encoding="utf-8").read()
        make_post_header_replacements(original_file_content, replacement_content)

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
