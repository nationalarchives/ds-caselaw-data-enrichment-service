import json
import logging
import re
from typing import Literal

import lxml.etree
from bs4 import BeautifulSoup

from replacer.replacer_pipeline import replacer_pipeline
from utils.types import (
    DocumentAsXMLString,
    Reference,
    Replacement,
    XMLFragmentAsString,
)

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

TAG_REMOVE_XSLT = """
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>
<xsl:strip-space elements="*"/>

<!-- identity transform -->
<xsl:template match="@*|node()">
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
</xsl:template>

<!-- delete ref tags with origin=TNA attribute -->
<xsl:template match="akn:ref[@uk:origin='TNA']">
    <xsl:apply-templates/>
</xsl:template>

<!-- delete ref tags with no origin attribute -->
<xsl:template match="akn:ref[not(@uk:origin)]">
    <xsl:apply-templates/>
</xsl:template>

</xsl:stylesheet>
"""


def make_post_header_replacements(
    original_content: DocumentAsXMLString,
    replacement_patterns: str,
) -> DocumentAsXMLString:
    """
    Replaces the content following a closing header tag in a legal document with new content.
    If there is no closing header tag, then we replace the full content.

    Note:
    - This function assumes a specific structure of the legal document with closing header tags.

    Args:
        original_content (str): The original content of the legal document
        replacement_patterns (str): The line separated replacement patterns

    Returns:
        str: The modified legal document content with the replacement applied.
    """
    cleaned_file_content = sanitize_judgment(original_content)
    pre_header, end_header_tag, post_header = split_text_by_closing_header_tag(cleaned_file_content)

    replaced_post_header_content = apply_replacements(post_header, replacement_patterns)
    LOGGER.info("Got post-header replacement text content")

    full_replaced_text_content = pre_header + end_header_tag + replaced_post_header_content

    return DocumentAsXMLString(full_replaced_text_content)


def apply_replacements(content: XMLFragmentAsString, replacement_patterns: str) -> XMLFragmentAsString:
    """
    Run the replacer pipeline to make replacements on caselaw, legislation and abbreviations
    """

    case_replacement_patterns: list[Replacement] = []
    leg_replacement_patterns: list[Replacement] = []
    abb_replacement_patterns: list[Replacement] = []

    for replacement_pattern_json in replacement_patterns.splitlines():
        LOGGER.debug(replacement_pattern_json)
        replacement_pattern_dict = json.loads(replacement_pattern_json)

        replacement_type, replacement_pattern_list = list(replacement_pattern_dict.items())[0]
        replacement_pattern = tuple(replacement_pattern_list)

        if replacement_type == "case":
            case_replacement_patterns.append(replacement_pattern)

        elif replacement_type == "leg":
            leg_replacement_patterns.append(replacement_pattern)

        elif replacement_type == "abb":
            abb_replacement_patterns.append(replacement_pattern)

    file_data_enriched = replacer_pipeline(
        content,
        case_replacement_patterns,
        leg_replacement_patterns,
        abb_replacement_patterns,
    )

    LOGGER.info("Content enriched")

    return file_data_enriched


def detect_reference(text: str, etype: Literal["legislation"]) -> Reference:
    """
    Detect citation references.
    :param text: text to be searched for references
    :param etype: type of reference to be detected
    :returns references: List(Tuple[((start, end), detected_ref)]), of detected legislation
    """
    patterns = {
        "legislation": r"<ref(((?!ref>).)*)(.*?)ref>",
    }

    references = [(m.span(), m.group()) for m in re.finditer(patterns[etype], text)]
    return references


def sanitize_judgment(file_content: DocumentAsXMLString) -> DocumentAsXMLString:
    file_content = _remove_old_enrichment_references(file_content)

    soup = BeautifulSoup(file_content, "xml")

    for element in soup.find_all("FRBRdate", {"name": "tna-enriched"}):
        element.decompose()
    for element in soup.find_all("uk:tna-enrichment-engine"):
        element.decompose()

    return DocumentAsXMLString(str(soup))


def _remove_old_enrichment_references(
    file_content: DocumentAsXMLString,
) -> DocumentAsXMLString:
    """
    Enrichment creates <ref uk:origin="TNA"> tags; delete these.
    vCite enrichment created <ref> tags with no uk:origin, delete these too.
    """
    root = lxml.etree.fromstring(file_content.encode("utf-8"))

    transform = lxml.etree.XSLT(lxml.etree.XML(TAG_REMOVE_XSLT))

    result = transform(root)

    return DocumentAsXMLString(lxml.etree.tostring(result).decode("utf-8"))


def split_text_by_closing_header_tag(
    content: DocumentAsXMLString,
) -> tuple[XMLFragmentAsString, XMLFragmentAsString, XMLFragmentAsString]:
    """
    Split content into start, closing header tag and body
    to ensure replacements only occur in the body.
    """
    header_patterns = [r"</header>", r"<header/>"]
    for pattern in header_patterns:
        if pattern not in content:
            continue

        return (
            XMLFragmentAsString(content.partition(pattern)[0]),
            XMLFragmentAsString(content.partition(pattern)[1]),
            XMLFragmentAsString(content.partition(pattern)[2]),
        )  # This cannot be a list comprehension because we need to know the length of the tuple
    return (
        XMLFragmentAsString(""),
        XMLFragmentAsString(""),
        XMLFragmentAsString(content),
    )
