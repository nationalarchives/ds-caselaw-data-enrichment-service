import re, os
from bs4 import BeautifulSoup

"""
This code handles the link of oblique references (i.e 'the Act' or 'the 1977 Act'). This is done in the following way:
1. We use the previously enriched judgment and identify where there are legislation xrefs in the judgment body.
2. We search for 'T(t)he/T(t)his/T(t)hat Act' and 'T(t)he/T(t)his/T(t)hat [dddd] Act' references in the judgment text.
3. If the matched oblique reference does not contain a year, we use the location of the oblique reference and 'legislation' reference 
to find which legislation the oblique reference is closest to, and then link to that legislation.
4. If the matched oblique reference contains a year, we search for the matched 'legislation' (found in 1.) that corresponds to that year
and then link to that legislation.
5. We build a replacement string that wraps the detected oblique reference into a <ref> element with the link and canonical form of the linked legislation as attributes. 

The pipeline returns a dictionary containing the detected oblique reference, its position and the replacement string.
"""

patterns = {
    "legislation": r"<ref(((?!ref>).)*)type=\"legislation\"(.*?)ref>",
    "numbered_act": r"(the|this|that|The|This|That)\s([0-9]{4})\s(Act)",
    "act": r"(the|this|that|The|This|That)\s(Act)",
}


def detect_reference(text, etype):
    """
    Detect legislation and oblique references.
    :param text: text to be searched for references
    :param etype: type of reference to be detected
    :returns: list of detected references
    """
    references = [(m.span(), m.group()) for m in re.finditer(patterns[etype], text)]

    return references


def create_legislation_dict(leg_references):
    """
    Create a dictionary containing metadata of the detected 'legislation' reference
    :param leg_references: list of legislation references found in the judgment and their location
    :returns: list of legislation dictionaries
    """
    legislation_dicts = []

    for leg_ref in leg_references:
        legislation_dict = {}
        soup = BeautifulSoup(leg_ref[1], "xml")
        ref = soup.find("ref")
        leg_name = ref.text
        leg_year = re.search("\d{4}", leg_name).group(0)
        href = ref["href"]
        canonical = ref["canonical"]
        legislation_dict["pos"] = leg_ref[0]
        legislation_dict["detected_leg"] = leg_name
        legislation_dict["href"] = href
        legislation_dict["canonical"] = canonical
        legislation_dict["year"] = leg_year
        legislation_dicts.append(legislation_dict)

    return legislation_dicts


def match_numbered_act(detected_numbered_act, legislation_dicts):
    """
    Match oblique references containing a year
    :param detected_numbered_act: detected oblique reference
    :param legislation_dicts: list of legislation dictionaries
    :returns: matched legislation dictionary
    """
    act_year = re.search("\d{4}", detected_numbered_act[1]).group(0)
    for leg_dict in legislation_dicts:
        if leg_dict["year"] == act_year:

            return leg_dict


def match_act(detected_act, legislation_dicts):
    """
    Match oblique references without a year
    :param detected_act: detected oblique reference
    :param legislation_dicts: list of legislation dictionaries
    :returns: matched legislation dictionary
    """
    eligble_references = []
    act_pos = detected_act[0][0]
    for leg_dict in legislation_dicts:
        if leg_dict["pos"][0] < act_pos:
            eligble_references.append(leg_dict)

    positions = []
    for eligble_ref in eligble_references:
        positions.append(eligble_ref["pos"][0])
    if positions:
        correct_pos = max(positions)
        correct_ref = [
            ref for ref in eligble_references if ref["pos"][0] == correct_pos
        ][0]
    else:
        correct_ref = []

    return correct_ref


def create_section_ref_tag(replacement_dict, match):
    """
    Create replacement string for detected oblique reference
    :param replacement_dict: legislation dictionary for replacement
    :param match: detected oblique reference
    :returns: replacement string
    """
    canonical = replacement_dict["canonical"]
    href = replacement_dict["href"]
    oblique_ref = f'<ref href="{href}" uk:canonical="{canonical}" uk:type="legislation">{match.strip()}</ref>'

    return oblique_ref


def get_replacements(detected_acts, legislation_dicts, numbered_act, replacements):
    """
    Create replacement string for detected oblique reference
    :param detected_acts: detected oblique references
    :param numbered_act: detected numbered oblique reference
    :param legislation_dicts: list of legislation dictionaries
    :param replacements: list of replacements
    :returns: list of replacements
    """
    for detected_act in detected_acts:
        replacement_dict = {}
        match = detected_act[1]
        if numbered_act:
            matched_replacement = match_numbered_act(detected_act, legislation_dicts)
        else:
            matched_replacement = match_act(detected_act, legislation_dicts)
        replacement_dict["detected_ref"] = match
        replacement_dict["ref_position"] = detected_act[0][0]
        if matched_replacement:
            replacement_dict["ref_tag"] = create_section_ref_tag(
                matched_replacement, match
            )
            replacements.append(replacement_dict)

    return replacements


def oblique_pipeline(file_data):
    """
    Create replacement string for detected oblique reference
    :param file_data: file content
    :returns: list of dictionaries containing detected oblique references and replacement strings
    """
    soup = BeautifulSoup(file_data, "xml")
    text = soup.find_all("p")
    text = "".join([str(p) for p in text])

    detected_leg = detect_reference(text, "legislation")
    legislation_dicts = create_legislation_dict(detected_leg)

    detected_numbered_acts = detect_reference(text, "numbered_act")
    detected_acts = detect_reference(text, "act")

    replacements = []
    replacements = get_replacements(
        detected_acts, legislation_dicts, False, replacements
    )
    replacements = get_replacements(
        detected_numbered_acts, legislation_dicts, True, replacements
    )

    for replacement in replacements:
        print(f"  => {replacement['detected_ref']} \t {replacement['ref_tag']}")

    return replacements
