import json
import logging
import re
from typing import List

from bs4 import BeautifulSoup

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


def make_post_header_replacements(
    original_content: str, post_header_replacement_content: str
) -> str:
    """
    Replaces the content following a closing header tag in a legal document with new content.
    If there is no closing header tag, then we replace the full content.

    Note:
    - This function assumes a specific structure of the legal document with closing header tags.

    Args:
        original_content (str): The original content of the legal document.
        post_header_replacement_content (str): The replacement content to insert after the header.

    Returns:
        str: The modified legal document content with the replacement applied.
    """
    cleaned_file_content = sanitize_judgment(original_content)
    document_split_by_header = split_text_by_closing_header_tag(cleaned_file_content)

    post_header_content = document_split_by_header[2]

    replaced_post_header_content = replace_text_content(
        post_header_content, post_header_replacement_content
    )
    LOGGER.info("Got post-header replacement text content")
    print(replaced_post_header_content)

    document_split_by_header[2] = replaced_post_header_content
    full_replaced_text_content = "".join(document_split_by_header)

    return full_replaced_text_content


def replace_text_content(file_content, replacements_content):
    """
    Run the replacer pipeline to make replacements on caselaw, legislation and abbreviations
    """
    replacements = []

    replacement_tuples_case = []
    replacement_tuples_leg = []
    replacement_tuples_abb = []

    tuple_file = replacements_content
    LOGGER.info("tuple_file")
    print(tuple_file)
    LOGGER.info("---lines--")

    for line in tuple_file.splitlines():
        LOGGER.debug(line)
        replacements.append(json.loads(line))

    for i in replacements:
        key, value = list(i.items())[0]

        LOGGER.info("replacements")
        if key == "case":
            case_law_tuple = tuple(i["case"])
            replacement_tuples_case.append(case_law_tuple)

        elif key == "leg":
            leg_tuple = tuple(i["leg"])
            replacement_tuples_leg.append(leg_tuple)

        else:
            abb_tuple = tuple(i["abb"])
            replacement_tuples_abb.append(abb_tuple)

    LOGGER.info("Replacement caselaw")
    print(replacement_tuples_case)

    from replacer.replacer_pipeline import replacer_pipeline

    file_data_enriched = replacer_pipeline(
        file_content,
        replacement_tuples_case,
        replacement_tuples_leg,
        replacement_tuples_abb,
    )
    LOGGER.info("Judgment enriched")

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
    remove_from_judgment = []
    list_of_references = detect_reference(file_content, "legislation")
    for i in list_of_references:
        opening = i[1].split(">")[0] + ">"
        remove_from_judgment.append((opening, ""))
        remove_from_judgment.append(("</ref>", ""))

    for k, v in remove_from_judgment:
        file_content = file_content.replace(k, v)

    soup = BeautifulSoup(file_content, "xml")
    enriched_date = soup.find_all("FRBRdate", {"name": "tna-enriched"})
    if enriched_date:
        for i in enriched_date:
            i.decompose()
    engine_version = soup.find_all("uk:tna-enrichment-engine")
    if engine_version:
        for i in engine_version:
            i.decompose()

    soup_string = str(soup)

    return soup_string


def split_text_by_closing_header_tag(file_content: str) -> List[str]:
    """
    Split file_content into start, closing header tag and body
    to ensure replacements only occur in the body.
    """
    header_patterns = [r"</header>", r"<header/>"]
    for pattern in header_patterns:
        if pattern in file_content:
            return re.split(f"({pattern})", file_content)
    return ["", "", file_content]
