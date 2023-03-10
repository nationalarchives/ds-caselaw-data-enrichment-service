"""Module containing the function that enriches oblique references"""

from bs4 import BeautifulSoup

from oblique_references.oblique_references import oblique_pipeline
from replacer.second_stage_replacer import replace_references_by_paragraph


def enrich_oblique_references(file_content: str) -> str:
    """
    Determines oblique references in the file_content and then returns
        an enriched file content with the replacements applied
    :param file_content: original file content
    :return: updated file content with enriched oblique references
    """
    resolved_refs = oblique_pipeline(file_content)
    if not resolved_refs:
        return file_content
    soup = BeautifulSoup(file_content, "xml")
    return replace_references_by_paragraph(soup, resolved_refs)
