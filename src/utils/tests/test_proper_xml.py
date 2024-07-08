import pytest

from utils.compare_xml import assert_equal_xml
from utils.proper_xml import create_tag_string


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
