"""
This code handles the link of provisions (i.e sections) to legislation. This is done in the following way:
1. We use the previously enriched judgment and identify where there are legislation xrefs in paragraphs.
2. We then search for and 'section' references in that paragraph.
3. We then use the location of the 'section' reference and 'legislation' reference to find which legislation the
section is closest to, and then link the section to that legislation.
4. We handle re-definition of sections by keeping track of the paragraph number when identifying xrefs and sections.
We use the paragraph number when replacing and only add the link to the section when we are after where the section was last defined.
If it is re-defined at a later paragraph, we would then use that new link instead from the paragraph number onwards.
To do:
1. "Sections 18-19" - we currently on replace sections 18 with a link to 18
2. "Section 27(A)" - currently miss these references when replacing
3. Sub-sections aren't being replaced
"""

import re
from typing import Any

import numpy as np
from bs4 import BeautifulSoup, Tag

from utils.custom_types import DocumentAsXMLString
from utils.proper_xml import create_tag_string

SectionDict = dict[str, list[Any]]  # this is a guess

THR = 30
keys = ["detected_ref", "ref_para", "ref_position", "ref_tag"]
patterns = {
    "legislation": r"<ref(((?!ref>).)*)type=\"legislation\"(.*?)ref>",
    "section": r"([sS]ection\W*[0-9]+(?=)|[sS]ections\W*[0-9]+(?=)|\b[sS]+\W*[0-9]+(?=))(\W*\([0-9]+\))?",
    "sub_section": r"\([0-9]+\)",
}


def detect_reference(text, etype="legislation"):
    """
    Detect legislation and section references.
    :param text: text to be searched for references
    :param etype: type of reference to be detected
    :returns references: List(Tuple[((start, end), detected_ref)]), of detected legislation
    """
    references = [(m.span(), m.group()) for m in re.finditer(patterns[etype], text)]
    return references


def find_closest_legislation(legislations, sections, thr=30):
    """
    Find the closest legislation to the section. This means that the section is likely a section from that piece of legislation.
    :param legislations: list of legislation references found in the paragraph, and their location
    :param sections: list of section references found in the paragraph, and their location
    :returns sections_to_leg: (section, legislation, sect_starting_position)
    """
    # gets positions of refs
    sec_pos = np.asarray([x[0] for x in sections])
    leg_pos = np.asarray([x[0] for x in legislations])

    # calculates distance between legislations and sections
    dist1 = sec_pos[:, 0][:, None] - leg_pos[:, 1]
    dist2 = leg_pos[:, 0] - sec_pos[:, 1][:, None]
    dist = dist1 * (dist1 > 0) + dist2 * (dist2 > 0)

    # returns sections that are within a threshold distance from legs
    matching_index_pairs: list[tuple[int, int]] = [tuple(row) for row in np.argwhere(dist < thr).tolist()]
    section_to_leg = [
        (sections[section_idx][1], legislations[legislation_idx][1], sections[section_idx][0][0])
        for section_idx, legislation_idx in matching_index_pairs
    ]
    return section_to_leg


def get_clean_section_number(section: str) -> str:
    """
    Cleans just the section number.
    :param section: section to return the number for
    :returns section_number: returns numbers from section as a string
    """
    section_number = re.findall(r"\d+", section)
    return section_number[0]


def save_section_to_dict(section_dict, para_number, clean_section_dict):
    """
    Saves the section and the relevant information to the master dictionary of all sections in the judgment.
    :param section_dict: current section information for the paragraph
    :param clean_section_dict: master dictionary of all sections in the judgment
    :param para_number: number of the paragraph in the judgment
    :returns clean_section_dict: master dictionary with addition of new definitions for sections in the judgment
    """
    # for each section found in the paragraph
    for section, full_ref, pos in section_dict:
        section_number = get_clean_section_number(section)
        soup = BeautifulSoup(full_ref, "xml")
        ref = soup.find("ref")
        if not isinstance(ref, Tag):
            msg = "Did not successfully get <ref> tag"
            raise ValueError(msg)
        canonical = ref.get("canonical")  # get the legislation canonical form
        leg_href = ref.get("href")  # get the legislation href
        section_href = str(leg_href) + "/section/" + str(section_number)  # creates the section href
        clean_section = "section " + str(section_number)

        # creates the canonical form for subsection
        sub_canonical = f"{canonical} s. {section_number}" if canonical else ""

        # new dictionary with the relevant information for the entry
        new_definition = {
            "para_number": para_number,
            "section_position": pos,
            "section_href": section_href,
            "section_canonical": sub_canonical,
            "ref": ref,
            "leg_href": leg_href,
            "canonical": canonical,
        }

        # isn't currently in the master dictionary
        if clean_section not in clean_section_dict.keys():
            clean_section_dict[clean_section] = [new_definition]

        else:
            # if it is, add the new definition to the list of definitions attached to the section. This means it has been re-defined at a later paragraph.
            value = clean_section_dict[clean_section]
            value.append(new_definition)
            clean_section_dict[clean_section] = value
    return clean_section_dict


def create_sub_section_links(section_dict, match):
    """
    Generates the links for any sub-sections in the judgment.
    :param section_dict: individual dictionary for the current section
    :param match: the section reference found in the paragraph
    :returns new_section_dict: section_dict with replaces href with new_href
    """
    new_section_dict = section_dict.copy()
    curr_href = new_section_dict["section_href"]
    # get the sub-section number
    sub_section = re.findall(patterns["sub_section"], match)
    # get the number itself
    sub_section_number = get_clean_section_number(sub_section[0])
    new_href = curr_href + "/" + str(sub_section_number)
    # replace href in section_dict with new_href
    new_section_dict["section_href"] = new_href

    return new_section_dict


def create_section_ref_tag(section_dict, match):
    """
    Generates the <ref> tag for a section in the judgment.
    :param section_dict: individual dictionary for the current section
    :param match: the section reference found in the paragraph
    :returns section_ref: string of ref to be inserted in XML
    """
    canonical = section_dict["section_canonical"]
    href = section_dict["section_href"]
    section_ref = create_tag_string(
        "ref",
        match.strip(),
        {
            "uk:type": "legislation",
            "href": href,
            "uk:canonical": canonical,
            "uk:origin": "TNA",
        },
    )
    return section_ref


def check_if_sub_section(section):
    """
    Check if the current reference is a sub-section.
    :param section: the section to check
    :returns: match object if sub section
    """
    return re.search(patterns["sub_section"], section)


def get_correct_section_def(section_matches, cur_para_number, cur_pos):
    """
    Performs the check if the current reference has been redefined and returns the correct reference by using the paragraph number.
    :param section_matches: list of dictionaries that include where that section has been redefined
    :param para_number: the number of the paragraph in the judgment
    """
    pos_refs = np.asarray([(match["para_number"], match["section_position"]) for match in section_matches])
    para_numbers = pos_refs[:, 0]

    # Get the closest paragraph with a previous mention of the match
    idx = (np.abs(para_numbers - cur_para_number)).argmin()
    candidates = [match for match in section_matches if match["para_number"] == para_numbers[idx]]
    if len(candidates) == 1:
        return candidates[0]
    else:
        # same as above; relies on position within a paragraph if the section is redefined within the paragraph.
        positions = pos_refs[:, 1]
        idx = (np.abs(positions - cur_pos)).argmin()
        return [match for match in section_matches if match["section_position"] == positions[idx]][0]


def provision_resolver(section_dict, matches, para_number):
    """
    Matches a section found in the judgment to the correct legislation, and provides necessary information for the replacements.
    :param section_dict: master dictionary of all sections in the judgment
    :param matches: list of the matches for the section references
    :param para_number: current paragraph number in the judgment
    :returns resolved_refs: list of dictionaries with the information for the replacements
    """
    resolved_refs = []
    # for each section found in the paragraph
    for pos, match in matches:
        clean_section_num = get_clean_section_number(match)
        clean_section = "section " + str(clean_section_num)

        # check if we have a match for the section that we've found
        if clean_section in section_dict.keys():
            values = section_dict[clean_section]
            # if they referred to the section before it was defined in a paragraph with linked leg, skip
            if para_number < values[0]["para_number"]:
                # TODO: double check logic here - probably redundant cuz of the prev. if stat.
                print("ERROR: THIS SHOULDN'T HAPPEN!")
                continue

            # if the section was re-defined (aka there is more than one dictionary), handle this
            if len(values) > 1:
                correct_reference = get_correct_section_def(values, para_number, pos[0])

            else:
                correct_reference = values[0]

            # check if this was a sub_section - as we only initially match to sections to create master dictionary
            if check_if_sub_section(match):
                correct_reference = create_sub_section_links(correct_reference, match)

            # create a <ref> tag for detected provision
            correct_reference["section_ref"] = create_section_ref_tag(correct_reference, match)

            resolved_refs.append(
                dict(
                    zip(
                        keys,
                        [match, para_number, pos[0], correct_reference["section_ref"]],
                        strict=False,
                    ),
                ),
            )
            print(f"  => {match} \t {para_number} \t {pos[0]} \t {correct_reference['section_ref']}")

    return resolved_refs


def provisions_pipeline(file_data: DocumentAsXMLString) -> list:
    """
    Matches all sections in the judgment to the correct legislation and provides necessary information for the replacements.
    :param file_data: file path of the judgment
    :returns resolved_refs: list of dictionaries with the information for the replacements in each section
    """
    soup = BeautifulSoup(file_data, "xml")
    text = soup.find_all("p")
    cur_para_number = 0
    section_dict: SectionDict = {}
    resolved_refs = []

    for line in text:
        sections = detect_reference(str(line), "section")
        if sections:
            legislations = detect_reference(str(line))
            if legislations:
                section_to_leg_matches = find_closest_legislation(legislations, sections, THR)

                # create the master section dictionary with relevant leg links
                section_dict = save_section_to_dict(section_to_leg_matches, cur_para_number, section_dict)

            # resolve sections to legislations
            resolved_refs.extend(provision_resolver(section_dict, sections, cur_para_number))

        cur_para_number += 1
    return resolved_refs
