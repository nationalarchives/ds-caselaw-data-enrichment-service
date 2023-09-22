import pytest

from replacer.make_replacments import split_text_by_closing_header_tag


class TestSplitTextByClosingHeaderTag:
    @pytest.mark.parametrize("closing_header_tag", ["</header>", "<header/>"])
    def test_split_text_by_closing_header_tag(self, closing_header_tag):
        file_content = f"ABC{closing_header_tag}DEF"
        assert split_text_by_closing_header_tag(file_content) == [
            "ABC",
            closing_header_tag,
            "DEF",
        ]

    @pytest.mark.parametrize("invalid_closing_header_tag", ["</foo>", "<foo/>"])
    def test_no_split(self, invalid_closing_header_tag):
        file_content = f"ABC{invalid_closing_header_tag}DEF"
        assert split_text_by_closing_header_tag(file_content) == ["", "", file_content]
