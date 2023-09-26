from pathlib import Path

import pytest

from replacer.make_replacments import (
    make_post_header_replacements,
    split_text_by_closing_header_tag,
)

FIXTURE_DIR = Path(__file__).parent.parent.resolve() / "fixtures/"


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
        assert content_with_replacements == expected_file_content.strip()


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
