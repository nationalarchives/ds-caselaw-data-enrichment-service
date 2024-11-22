import pytest

from utils.compare_xml import assert_equal_xml
from utils.proper_xml import create_tag_string, replace_string_with_tag


class TestReplaceStringWithTag:
    def test_as_text(self):
        assert_equal_xml(
            replace_string_with_tag("<p>In [2024] UKSC 1 ...</p>", "[2024] UKSC 1", "<ref blah='blah'>blah</ref>"),
            b'<p>In <ref blah="blah">blah</ref> ...</p>',
        )

    def test_as_text_multi(self):
        assert_equal_xml(
            replace_string_with_tag(
                "<p><span>[2024] UKSC 1</span><span>[2024] UKSC 1</span></p>",
                "[2024] UKSC 1",
                "<cite/>",
            ),
            b"<p><span><cite/></span><span><cite/></span></p>",
        )

    @pytest.mark.xfail
    def test_as_text_multi_in_tag(self):
        """Ideally, this should have <cite/> - <cite/> in the output; we could rerun until it runs clean"""
        assert_equal_xml(
            replace_string_with_tag("<p>[2024] UKSC 1 - [2024] UKSC 1</p>", "[2024] UKSC 1", "<cite/>"),
            b"<p><cite/> - [2024] UKSC 1</p>",
        )

    def test_as_attribute(self):
        assert_equal_xml(
            replace_string_with_tag(
                "<p>In <ref nc='[2024] UKSC 1'>the previous judgment</ref> ...</p>",
                "[2024] UKSC 1",
                "<ref blah='blah'>blah</ref>",
            ),
            b'<p>In <ref nc="[2024] UKSC 1">the previous judgment</ref> ...</p>',
        )


def test_simple_tag():
    assert_equal_xml(
        create_tag_string("kitten", "ocelot", {"panther": "cougar"}),
        b'<kitten xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" panther="cougar">ocelot</kitten>',
    )


def test_empty_tag():
    assert_equal_xml(
        create_tag_string("kitten"),
        b'<kitten xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"/>',
    )


def test_no_attrs():
    assert_equal_xml(
        create_tag_string("kitten", "ocelot"),
        b'<kitten xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">ocelot</kitten>',
    )


def test_empty_with_attrs():
    assert_equal_xml(
        create_tag_string("kitten", attrs={"panther": "cougar"}),
        b'<kitten xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" panther="cougar"/>',
    )


def test_namespaces():
    assert_equal_xml(
        create_tag_string("kitten", "ocelot", {"uk:panther": "cougar"}),
        b'<kitten xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:panther="cougar">ocelot</kitten>',
    )


def test_nested_xml():
    assert_equal_xml(
        create_tag_string("kitten", "a<b>c</b>e", {"uk:panther": "cougar"}),
        b'<kitten xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:panther="cougar">a<b>c</b>e</kitten>',
    )


def test_nested_xml_with_namespaces():
    assert_equal_xml(
        create_tag_string("kitten", "a<uk:b>c</uk:b>e", {"uk:panther": "cougar"}),
        b'<kitten xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:panther="cougar">a<uk:b>c</uk:b>e</kitten>',
    )


def test_mismatched_xml():
    with pytest.raises(AssertionError, match="xml mismatch at 7"):
        assert_equal_xml(create_tag_string("kitten"), create_tag_string("kittens"))
