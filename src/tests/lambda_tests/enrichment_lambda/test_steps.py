from pathlib import Path
from unittest.mock import Mock, patch

from lambdas.enrichment_lambda.steps import (
    make_post_header_replacements,
    replace_legislation_provisions,
)
from utils.compare_xml import assert_equal_xml


@patch("lambdas.enrichment_lambda.steps.provisions_pipeline", return_value=[])
def test_replace_legislation_provisions_returns_original_when_no_refs(_mock_pipeline):
    xml = "<akomaNtoso><judgment><p>No refs</p></judgment></akomaNtoso>"

    assert replace_legislation_provisions(xml) == xml


@patch("lambdas.enrichment_lambda.steps.replace_references_by_paragraph")
@patch("lambdas.enrichment_lambda.steps.provisions_pipeline", return_value=[((1, 2), "ref")])
def test_replace_legislation_provisions_applies_replacements(_mock_pipeline, mock_replace):
    replaced = Mock()
    replaced.__str__ = Mock(return_value="<akomaNtoso><judgment><p>Updated</p></judgment></akomaNtoso>")
    mock_replace.return_value = replaced

    xml = "<akomaNtoso><judgment><p>Original</p></judgment></akomaNtoso>"

    result = replace_legislation_provisions(xml)

    assert result == "<akomaNtoso><judgment><p>Updated</p></judgment></akomaNtoso>"
    assert mock_replace.call_count == 1


FIXTURE_DIR = Path(__file__).parent.parent.parent.resolve() / "fixtures/"


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
        expected_file_content = '<?xml version="1.0" encoding="utf-8"?>\n<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:html="http://www.w3.org/1999/xhtml" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"><judgment name="judgment"><header/><judgmentBody><ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="b" uk:year="2008" uk:origin="TNA">a</ref></judgmentBody></judgment></akomaNtoso>'
        assert make_post_header_replacements(original_file_content, replacement_content) == expected_file_content
