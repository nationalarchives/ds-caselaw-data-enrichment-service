from pathlib import Path

import lxml.etree
import pytest

from replacer.make_replacments import (
    _remove_old_enrichment_references,
    make_post_header_replacements,
    split_text_by_closing_header_tag,
)

FIXTURE_DIR = Path(__file__).parent.parent.resolve() / "fixtures/"


def canonical_xml(text):
    """with thanks to https://stackoverflow.com/questions/52422385/python-3-xml-canonicalization"""
    val = (
        lxml.etree.tostring(lxml.etree.fromstring(text.encode("utf-8")), method="c14n2")
        .replace(b"\n", b"")
        .replace(b" ", b"")
    )
    return val


def assert_xml_same(a, b):
    assert canonical_xml(a.strip()) == canonical_xml(b.strip())


class TestMakePostHeaderReplacements:
    def test_make_post_header_replacements(self):
        original_file_content = open(
            f"{FIXTURE_DIR}/ewhc-ch-2023-257_original.xml", "r", encoding="utf-8"
        ).read()
        replacement_content = open(
            f"{FIXTURE_DIR}/ewhc-ch-2023-257_replacements.txt", "r", encoding="utf-8"
        ).read()
        expected_file_content = open(
            f"{FIXTURE_DIR}/ewhc-ch-2023-257_enriched_stage_1.xml",
            "r",
            encoding="utf-8",
        ).read()

        content_with_replacements = make_post_header_replacements(
            original_file_content, replacement_content
        )
        assert canonical_xml(content_with_replacements) == canonical_xml(
            expected_file_content.strip()
        )

    def test_post_header_works_if_already_enriched(self):
        original_file_content = open(
            f"{FIXTURE_DIR}/ewhc-ch-2023-257_enriched_stage_1.xml",
            "r",
            encoding="utf-8",
        ).read()
        replacement_content = open(
            f"{FIXTURE_DIR}/ewhc-ch-2023-257_replacements.txt", "r", encoding="utf-8"
        ).read()
        expected_file_content = open(
            f"{FIXTURE_DIR}/ewhc-ch-2023-257_enriched_stage_1.xml",
            "r",
            encoding="utf-8",
        ).read()

        content_with_replacements = make_post_header_replacements(
            original_file_content, replacement_content
        )

        assert_xml_same(content_with_replacements, expected_file_content)

    def test_remove_legislation_references(self):
        tidy_output = _remove_old_enrichment_references(
            """
            <xml xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0' xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <a><e><ref uk:origin="TNA"><ref uk:origin="TNA"><b>AAA</b></ref><c/></ref>D</e></a>
            </xml>"""
        )

        assert "<a><e><b>AAA</b><c/>D</e></a>" in tidy_output
        assert "not-TNA" in _remove_old_enrichment_references(
            '<akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"><ref uk:origin="not-TNA"></ref></akomaNtoso>'
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
