"""Module containing the function that enriches oblique references"""

from bs4 import BeautifulSoup
from shared.replacer.second_stage_replacer import (
    replace_references_by_paragraph,
)

from lambdas.determine_oblique_references.oblique_references.oblique_references import (
    get_oblique_reference_replacements_by_paragraph,
)


def enrich_oblique_references(file_content: str) -> str:
    """
    Determines oblique references in the file_content and then returns
        an enriched file content with the replacements applied
    :param file_content: original file content
    :return: updated file content with enriched oblique references
    """
    oblique_reference_replacements = get_oblique_reference_replacements_by_paragraph(
        file_content
    )
    if not oblique_reference_replacements:
        return file_content
    soup = BeautifulSoup(file_content, "xml")
    return replace_references_by_paragraph(soup, oblique_reference_replacements)
