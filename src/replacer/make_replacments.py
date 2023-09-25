import json
import logging
import re
from typing import Tuple

from bs4 import BeautifulSoup

from replacer.replacer_pipeline import replacer_pipeline

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def make_post_header_replacements(
    original_content: str, replacement_patterns: str
) -> str:
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
    pre_header, end_header_tag, post_header = split_text_by_closing_header_tag(
        cleaned_file_content
    )

    replaced_post_header_content = apply_replacements(post_header, replacement_patterns)
    LOGGER.info("Got post-header replacement text content")

    full_replaced_text_content = (
        pre_header + end_header_tag + replaced_post_header_content
    )

    return full_replaced_text_content


def apply_replacements(content: str, replacement_patterns: str) -> str:
    """
    Run the replacer pipeline to make replacements on caselaw, legislation and abbreviations
    """

    case_replacement_patterns = []
    leg_replacement_patterns = []
    abb_replacement_patterns = []

    for replacement_pattern_json in replacement_patterns.splitlines():
        LOGGER.debug(replacement_pattern_json)
        replacement_pattern_dict = json.loads(replacement_pattern_json)

        replacement_type, replacement_pattern_list = list(
            replacement_pattern_dict.items()
        )[0]
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


def detect_reference(text, etype):
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


def sanitize_judgment(file_content):
    file_content = _remove_legislation_references(file_content)

    soup = BeautifulSoup(file_content, "xml")

    _decompose_elements(soup, "FRBRdate", {"name": "tna-enriched"})
    _decompose_elements(soup, "uk:tna-enrichment-engine")

    soup_string = str(soup)

    return soup_string


def _decompose_elements(soup, *element_kwargs):
    elements = soup.find_all(*element_kwargs)
    for element in elements:
        element.decompose()


def _remove_legislation_references(file_content):
    remove_from_judgment = []
    legislation_references = detect_reference(file_content, "legislation")
    for reference in legislation_references:
        canonical_reference = reference[1]
        opening = canonical_reference.split(">")[0] + ">"
        remove_from_judgment.append((opening, ""))
        remove_from_judgment.append(("</ref>", ""))

    for k, v in remove_from_judgment:
        file_content = file_content.replace(k, v)
    return file_content


def split_text_by_closing_header_tag(content: str) -> Tuple[str, str, str]:
    """
    Split content into start, closing header tag and body
    to ensure replacements only occur in the body.
    """
    header_patterns = [r"</header>", r"<header/>"]
    for pattern in header_patterns:
        if pattern not in content:
            continue
        return content.partition(pattern)
    return "", "", content
