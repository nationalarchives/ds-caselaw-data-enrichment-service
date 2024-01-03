"""
@author: editha.nemsic
This code handles the link of oblique references (i.e 'the Act' or 'the 1977 Act').

This is done in the following way:
1. We use the previously enriched judgment and identify where there are legislation
    xrefs in the judgment body.
2. We search for 'T(t)he/T(t)his/T(t)hat Act' and 'T(t)he/T(t)his/T(t)hat [dddd] Act'
    references in the judgment text.
3. If the matched oblique reference does not contain a year, we use the location of the
    oblique reference and 'legislation' reference to find which legislation the oblique
    reference is closest to, and then link to that legislation.
4. If the matched oblique reference contains a year, we search for the matched
    'legislation' (found in 1.) that corresponds to that year and then link to that legislation.
5. We build a replacement string that wraps the detected oblique reference into a <ref>
    element with the link and canonical form of the linked legislation as attributes.

The pipeline returns a dictionary containing the detected oblique reference, its
    position and the replacement string.
"""

import re
from typing import Dict, List, TypedDict, Union

from bs4 import BeautifulSoup

from utils.proper_xml import create_tag_string

LegislationReference = tuple[tuple[int, int], str]


class LegislationDict(TypedDict):
    detected_leg: str
    year: str
    para: int
    para_pos: tuple[int, int]
    canonical: str
    href: str


LegislationReferenceReplacements = List[Dict[str, Union[str, int]]]


class NotExactlyOneRefTag(RuntimeError):
    """soup.get() can return None if there is no <ref> tag to find, or
    a list of hits if there are multiple tags. These are not handled
    correctly."""


patterns = {
    "legislation": r"<ref(((?!ref>).)*)type=\"legislation\"(.*?)ref>",
    "numbered_act": r"(the|this|that|The|This|That)\s([0-9]{4})\s(Act)",
    "act": r"(the|this|that|The|This|That)\s(Act)",
}


def detect_reference(text: str, etype: str) -> List[LegislationReference]:
    """
    Detect legislation and oblique references.
    :param text: text to be searched for references
    :param etype: type of reference to be detected
    :returns: list of detected references
    """
    references = [(m.span(), m.group()) for m in re.finditer(patterns[etype], text)]
    return references


def create_legislation_dict(
    legislation_references: List[LegislationReference], paragraph_number: int
) -> List[LegislationDict]:
    """
    Create a dictionary containing metadata of the detected 'legislation' reference
    :param legislation_references: list of legislation references found in the judgment
        and their location
    :param paragraph_number: paragraph number the legislation reference was found in
    :returns: list of legislation dictionaries
    """
    legislation_dicts: list[LegislationDict] = []

    for legislation_reference in legislation_references:
        soup = BeautifulSoup(legislation_reference[1], "xml")
        ref = soup.ref
        if not ref:
            continue
        legislation_name = ref.text if not None else ""

        href = ref.get("href")
        canonical = ref.get("canonical")

        if not isinstance(href, str):
            raise NotExactlyOneRefTag(
                f"Legislation reference {legislation_reference!r} does not have exactly one 'href', paragraph {paragraph_number}"
            )
        if not isinstance(canonical, str):
            raise NotExactlyOneRefTag(
                f"Legislation reference {legislation_reference!r} does not have exactly one 'canonical', paragraph {paragraph_number}"
            )

        legislation_dict: LegislationDict = {
            "para": paragraph_number,
            "para_pos": legislation_reference[0],
            "detected_leg": legislation_name,
            "href": href,
            "canonical": canonical,
            "year": _get_legislation_year(legislation_name),
        }

        legislation_dicts.append(legislation_dict)

    return legislation_dicts


def _get_legislation_year(legislation_name: str) -> str:
    legislation_year_match = re.search(r"\d{4}", legislation_name)
    if not legislation_year_match:
        return ""
    return legislation_year_match.group()


def match_numbered_act(
    detected_numbered_act: LegislationReference,
    legislation_dicts: List[LegislationDict],
) -> LegislationDict | None:
    """
    Match oblique references containing a year
    :param detected_numbered_act: detected oblique reference
    :param legislation_dicts: list of legislation dictionaries
    :returns: matched legislation dictionary
    """
    act_year_match = re.search(r"\d{4}", detected_numbered_act[1])
    if not act_year_match:
        return None

    act_year = act_year_match.group(0)
    for leg_dict in legislation_dicts:
        if leg_dict["year"] == act_year:
            return leg_dict
    return None


def match_act(
    oblique_act: LegislationReference,
    legislation_dicts: List[LegislationDict],
    paragraph_number: int,
) -> LegislationDict | None:
    """
    Match oblique references without a year
    :param detected_act: detected oblique reference
    :param legislation_dicts: list of legislation dictionaries
    :param paragraph_number: paragraph number the legislation reference was found in
    :returns: matched legislation dictionary
    """
    oblique_act_para_pos = oblique_act[0][0]
    eligible_legislation = [
        leg_dict
        for leg_dict in legislation_dicts
        if (
            leg_dict["para"] < paragraph_number
            or (
                leg_dict["para"] == paragraph_number
                and leg_dict["para_pos"][0] < oblique_act_para_pos
            )
        )
    ]

    if not eligible_legislation:
        return None

    legislation_to_match = eligible_legislation[-1]
    legislation_to_match_position = legislation_to_match["para_pos"][0]

    # TODO: filter because we could have multiple??? is this true or unneeded?
    matched_act = [
        legislation
        for legislation in eligible_legislation
        if legislation["para_pos"][0] == legislation_to_match_position
    ][0]

    return matched_act


def create_section_ref_tag(replacement_dict: LegislationDict, match: str) -> str:
    """
    Create replacement string for detected oblique reference
    :param replacement_dict: legislation dictionary for replacement
    :param match: detected oblique reference
    :returns: replacement string
    """
    canonical = replacement_dict["canonical"]
    href = replacement_dict["href"]
    oblique_ref = create_tag_string(
        "ref",
        match.strip(),
        {
            "href": href,
            "uk:canonical": canonical,
            "uk:type": "legislation",
            "uk:origin": "TNA",
        },
    )
    return oblique_ref


def get_replacements(
    detected_acts: List[LegislationReference],
    legislation_dicts: List[LegislationDict],
    numbered_act: bool,
    replacements: List[Dict],
    paragraph_number: int,
) -> LegislationReferenceReplacements:
    """
    Create replacement string for detected oblique reference
    :param detected_acts: detected oblique references
    :param numbered_act: detected numbered oblique reference
    :param legislation_dicts: list of legislation dictionaries
    :param replacements: list of replacements
    :param paragraph_number: paragraph number the legislation reference was found in
    :returns: list of replacements
    """
    for detected_act in detected_acts:
        replacement_dict: Dict[str, Union[str, int]] = {}
        match = detected_act[1]
        if numbered_act:
            matched_replacement = match_numbered_act(detected_act, legislation_dicts)
        else:
            matched_replacement = match_act(
                detected_act, legislation_dicts, paragraph_number
            )
        replacement_dict["detected_ref"] = match
        replacement_dict["ref_position"] = detected_act[0][0]
        replacement_dict["ref_para"] = paragraph_number
        if matched_replacement:
            replacement_dict["ref_tag"] = create_section_ref_tag(
                matched_replacement, match
            )
            replacements.append(replacement_dict)

    return replacements


def get_oblique_reference_replacements_by_paragraph(
    file_content: str,
) -> LegislationReferenceReplacements:
    """
    Determines oblique references and replacement strings grouped by paragraph
    :param file_content: original judgment file content
    :returns: list of dictionaries containing detected oblique
        references and replacement strings
    """
    soup = BeautifulSoup(file_content, "xml")
    paragraphs = soup.find_all("p")
    all_replacements: List[Dict] = []
    all_legislation_dicts = []

    for paragraph_number, paragraph in enumerate(paragraphs):
        replacements: List[Dict] = []
        detected_legislation = detect_reference(str(paragraph), "legislation")
        legislation_dicts = create_legislation_dict(
            detected_legislation, paragraph_number
        )
        all_legislation_dicts.extend(legislation_dicts)

        detected_acts = detect_reference(str(paragraph), "act")
        if detected_acts:
            replacements = get_replacements(
                detected_acts,
                all_legislation_dicts,
                False,
                replacements,
                paragraph_number,
            )

        detected_numbered_acts = detect_reference(str(paragraph), "numbered_act")
        if detected_numbered_acts:
            replacements = get_replacements(
                detected_numbered_acts,
                all_legislation_dicts,
                True,
                replacements,
                paragraph_number,
            )

        all_replacements.extend(replacements)

    for replacement in all_replacements:
        print(
            f"  => {replacement['detected_ref']} \t {replacement['ref_tag']} \t Paragraph: {replacement['ref_para']} \t Position: {replacement['ref_position']}"
        )

    return all_replacements
