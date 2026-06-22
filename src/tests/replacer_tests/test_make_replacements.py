import pytest

from enrichment.replacer.make_replacements import (
    _remove_old_enrichment_references,
    split_text_by_closing_header_tag,
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


class TestRemoveOldEnrichmentReferences:
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
