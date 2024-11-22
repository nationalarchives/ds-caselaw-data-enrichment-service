"""
Replacer logic for first phase enrichment.
Handles the replacements of abbreviations, legislation, and case law.
"""

import html
import re

from utils.proper_xml import create_tag_string, replace_string_with_tag
from utils.types import Replacement, XMLFragmentAsString

JUNK_REGEX = r"</judgment>\s*</akomaNtoso>\s*$"
BAD = '="<'


def assert_not_bad(s):
    if BAD in s:
        msg = f"{BAD!r} found in XML"
        raise RuntimeError(msg)


def _replace_string_with_tag_handling_junk(file_data, string, tag):
    """The XML might contain </judgment></akomaNtoso> at the end; remove and replace if so."""

    junk = re.search(JUNK_REGEX, file_data)
    if junk:
        good = re.sub(JUNK_REGEX, "", file_data)
        tail = junk.group()
    else:
        good = file_data
        tail = ""

    new = replace_string_with_tag(good, string, tag)
    return new + tail


def fixed_year(year: str) -> str | None:
    """For some reason, years can be returned as "No Year", despite not being present in the code (outside tests) or the database
    (as far as I can see."""
    if not year:
        return None
    match = re.search(r"\d+", year)
    if match:
        return match.group()
    else:
        return None


def replacer_caselaw(file_data: XMLFragmentAsString, replacement: Replacement) -> XMLFragmentAsString:
    """
    String replacement in the XML
    :param file_data: XML file
    :param replacement: tuple of citation match and corrected citation
    :return: enriched XML file data
    """

    year = fixed_year(replacement[2])
    attribs = {
        "uk:type": "case",
        "href": replacement[3],
        "uk:isNeutral": str(replacement[4]).lower(),
        "uk:canonical": replacement[1],
    }
    if year:
        attribs["uk:year"] = year
    attribs["uk:origin"] = "TNA"

    replacement_tag = create_tag_string("ref", html.escape(replacement[0]), attribs)
    output = _replace_string_with_tag_handling_junk(file_data, replacement[0], replacement_tag)

    assert_not_bad(file_data)
    return output


def replacer_leg(file_data: XMLFragmentAsString, replacement: Replacement) -> XMLFragmentAsString:
    """
    String replacement in the XML
    :param file_data: XML file
    :param replacement: tuple of citation match and corrected citation
    :return: enriched XML file data
    """
    attribs = {
        "uk:type": "legislation",
        "href": replacement[1],
        "uk:canonical": replacement[2],
        "uk:origin": "TNA",
    }
    replacement_tag = create_tag_string("ref", html.escape(replacement[0]), attribs)
    output = _replace_string_with_tag_handling_junk(file_data, replacement[0], replacement_tag)
    assert_not_bad(file_data)
    return output


def replacer_abbr(file_data: XMLFragmentAsString, replacement: Replacement) -> XMLFragmentAsString:
    """
    String replacement in the XML
    :param file_data: XML file
    :param replacement: tuple of citation match and corrected citation
    :return: enriched XML file data
    """
    replacement_tag = f'<abbr title="{replacement[1]}" uk:origin="TNA">{replacement[0]}</abbr>'

    output = _replace_string_with_tag_handling_junk(file_data, replacement[0], replacement_tag)
    assert_not_bad(file_data)
    return output


def replacer_pipeline(
    file_data: XMLFragmentAsString,
    REPLACEMENTS_CASELAW: list[Replacement],
    REPLACEMENTS_LEG: list[Replacement],
    REPLACEMENTS_ABBR: list[Replacement],
) -> XMLFragmentAsString:
    """
    Pipeline to run replacer_caselaw, replacer_leg, replacer_abbr
    :param file_data: XML file
    :param REPLACEMENTS_CASELAW: list of unique tuples of citation match and corrected citation
    :param REPLACEMENTS_LEG: list of unique tuples of citation match and corrected citation
    :param REPLACEMENTS_ABBR: list of unique tuples of citation match and corrected citation
    :return: enriched XML file data
    """

    assert_not_bad(file_data)

    for replacement in list(set(REPLACEMENTS_CASELAW)):
        file_data = replacer_caselaw(file_data, replacement)
    assert_not_bad(file_data)

    for replacement in list(set(REPLACEMENTS_LEG)):
        file_data = replacer_leg(file_data, replacement)
    assert_not_bad(file_data)

    for replacement in list(set(REPLACEMENTS_ABBR)):
        file_data = replacer_abbr(file_data, replacement)
    assert_not_bad(file_data)

    return file_data
