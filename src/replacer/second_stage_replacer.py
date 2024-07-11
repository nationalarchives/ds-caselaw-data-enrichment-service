"""
Replacer logic for second and third phase enrichment.
Handles the replacements of oblique references and legislation provisions.
"""

import re
from collections.abc import Iterable
from itertools import groupby
from typing import TypedDict

from bs4 import BeautifulSoup, Tag

from utils.types import DocumentAsXMLString

LegislationReference = tuple[tuple[int, int], str]


class LegislationReferenceReplacement(TypedDict):
    detected_ref: str  # "the 2004 Act"
    ref_position: int
    ref_para: int
    ref_tag: str  # "<ref href='...'>the 2004 Act</ref>"


def split_string(text: str, split_points: list[int]) -> list[str]:
    """
    Splits a string at given points in the text
    :param text: some string of text
    :param split_points: list of positions to split between
    :return: list of split strings
    """
    return [text[slice(*x)] for x in zip(split_points, split_points[1:] + [None], strict=False)]


def replace_references(text: str, reference_replacements: list[LegislationReferenceReplacement]) -> str:
    """
    Replaces references in text according to the reference_replacements list
    :param text: original text string
    :param reference_replacements: list of dict of references and replacement information
    :return: string with replaced references
    """

    # Splitting the text fails if the points are not sorted
    reference_replacements = sorted(reference_replacements, key=lambda x: x["ref_position"])
    split_points: list[int] = [
        split_point
        for reference_replacement in reference_replacements
        if isinstance((split_point := reference_replacement.get("ref_position")), int)
    ]
    split_text = split_string(text, split_points)
    enriched_text = text[: split_points[0]]
    for sub_text, reference_replacement in zip(split_text, reference_replacements, strict=False):
        detected_ref = reference_replacement["detected_ref"]
        if not isinstance(detected_ref, str):
            continue
        ref_tag = reference_replacement["ref_tag"]
        if not isinstance(ref_tag, str):
            continue
        enriched_text += re.sub(
            re.escape(detected_ref),
            ref_tag,
            sub_text,
        )

    return enriched_text


def create_replacement_paragraph(
    paragraph_string: str,
    paragraph_reference_replacements: Iterable[LegislationReferenceReplacement],
) -> Tag:
    replacement_paragraph_string = replace_references(paragraph_string, list(paragraph_reference_replacements))
    wrapper = f'<xml xmlns:uk="placeholder">{replacement_paragraph_string}</xml>'
    replacement_paragraph = BeautifulSoup(wrapper, "xml").p
    if replacement_paragraph is None:
        raise RuntimeError(f"No paragraphs found in {replacement_paragraph_string}")
    return replacement_paragraph


def replace_references_by_paragraph(
    file_data: BeautifulSoup,
    reference_replacements: list[LegislationReferenceReplacement],
) -> DocumentAsXMLString:
    """
    Replaces references in the file_data xml by paragraph
    :param file_data: XML file
    :param reference_replacements: list of dict of detected references
    :return: enriched XML file data string
    """

    def key_func(k: LegislationReferenceReplacement) -> int:
        return k["ref_para"]

    paragraphs = file_data.find_all("p")
    ordered_reference_replacements = sorted(reference_replacements, key=key_func)

    for paragraph_number, paragraph_reference_replacements in groupby(ordered_reference_replacements, key=key_func):
        paragraph_string = str(paragraphs[paragraph_number])
        paragraphs[paragraph_number].replace_with(
            create_replacement_paragraph(paragraph_string, paragraph_reference_replacements),
        )
    return DocumentAsXMLString(str(file_data))
