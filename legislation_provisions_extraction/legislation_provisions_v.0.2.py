import re
import os
from bs4 import BeautifulSoup
import numpy as np

"""
This code handles the link of provisions (i.e sections) to legislation. This is done in the following way: 

1. We use the previously enriched judgment and identify where there are legislation xrefs in paragraphs. 
2. We then search for and 'section' references in that paragraph. 
3. We then use the location of the 'section' reference and 'legislation' reference to find which legislation the 
section is closest to, and then link the section to that legislation.
4. We handle re-definition of sections by keeping track of the paragraph number when identifying xrefs and sections. 
We use the paragraph number when replacing and only add the link to the section when we are after where the section was last defined. 
If it is re-defined at a later paragraph, we would then use that new link instead from the paragraph number onwards. 

The limitations of this method means that: 
1. There may be incorrect linking, this is seen in cases where the section is previously defined, and then appears
again in a paragraph with a different piece of legislation. Because it is the only explicit mention to legislation 
in that paragraph, this methodology assumes that the provision must be linked to that legislation. 

For example: "Section 1 refers to ... In the Puppies and Kittens Act, this has a different meaning ..." 

In this instance, the link will be generated to the Puppies and Kittens Act, despit the fact that it's 
"""
THR = 50
patterns = {
    'legislation': r'<ref(.*?)type=\"legislation\"(.*?)ref>',
    'section': r'( [sS]ection\W*[0-9]+(?=)|[sS]ections\W*[0-9]+| [sS]+\W*[0-9]+)(\W*\([0-9]+\))?',
    'sub_section': r'\([0-9]+\)'
}

"""
Detect legislation and section references. 
:param text: text to be searched for references
:param etype: type of reference to be detected
"""


def detect_reference(text, etype='legislation'):

    references = [(m.span(), m.group())
                  for m in re.finditer(patterns[etype], text)]
    # returns a list of tuples in the form [((start, end), detected_ref)]
    return references


"""
Find the closest legislation to the section. This means that the section is likely a section from that piece of legislation.
:param legislations: list of legislation references found in the paragraph, and their location
:param sections: list of section references found in the paragraph, and their location
"""


def find_closest_legislation(legislations, sections, thr=30):
    # section_dict = {}
    # current_match = {}

    # # iterate through each of the sections found in that paragraph
    # for section in sections:
    #     section_loc = section[0]
    #     section_loc_average = (section_loc[0] + section_loc[1])/2

    #     # iterate through the legislation found in the same para to find the closest
    #     for legislation in legislations:
    #         leg_loc = legislation[0]
    #         leg_loc_average = (leg_loc[0] + leg_loc[1])/2 # take the average of the start and end points of the legislation
    #         distance = abs(leg_loc_average - section_loc_average) # get the absolute distance between the two

    #         # first time the legislation is matched to the section
    #         if section[1] not in current_match.keys():
    #             current_match[section[1]] = {'legislation': legislation[1], 'distance': distance}
    #         else:
    #             # if the distance is closer, update the legislation
    #             if distance < current_match[section[1]]['distance']:
    #                 current_match[section[1]] = {'legislation': legislation[1], 'distance': distance}

    #     # save the legislation href to the section dictionary
    #     section_dict[section[1]] = current_match[section[1]]['legislation']

    sec_pos = np.asarray([x[0] for x in sections])
    leg_pos = np.asarray([x[0] for x in legislations])

    dist1 = sec_pos[:, 0][:, None] - leg_pos[:, 1]
    dist2 = leg_pos[:, 0] - sec_pos[:, 1][:, None]
    dist = dist1 * (dist1 > 0) + dist2 * (dist2 > 0)

    idx = np.argwhere(dist < thr)
    section_to_leg = [(sections[i][1], legislations[j][1],
                       sections[i][0][0]) for i, j in idx]
    return section_to_leg  # (section, legislation, sect_position)


"""
Cleans just the section number. 
:param section: section to return the number for
"""


def get_clean_section_number(section):
    section_number = re.findall(r'\d+', section)
    return section_number[0]


"""
Saves the section and the relevant information to the master dictionary of all sections in the judgment.
:param section_dict: current section information for the paragraph 
:param clean_section_dict: master dictionary of all sections in the judgment
:param para_number: number of the paragraph in the judgment
"""


def save_section_to_dict(section_dict, para_number, clean_section_dict):

    # for each section found in the paragraph
    for section, full_ref, pos in section_dict:

        section_number = get_clean_section_number(section)
        # full_ref = section_dict[section] # gets the full ref tag
        soup = BeautifulSoup(full_ref, 'xml')
        ref = soup.find('ref')
        leg_href = ref['href']  # get the legislation href
        section_href = str(leg_href) + "/section/" + \
            str(section_number)  # creates the section href
        canonical = ref.find('canonical')
        clean_section = "section " + str(section_number)

        # new dictionary with the relevant information for the entry
        new_definition = {'para_number': para_number,
                          'ref_position': pos,
                          'section_href': section_href,
                          'ref': ref,
                          'leg_href': leg_href,
                          'canonical': canonical}

        # isn't currently in the master dictionary
        if clean_section not in clean_section_dict.keys():
            clean_section_dict[clean_section] = [new_definition]

        else:
            # if it is, add the new definition to the list of definitions attached to the section. This means it has been re-defined at a later paragraph.
            value = clean_section_dict[clean_section]
            value.append(new_definition)
            clean_section_dict[clean_section] = value

    # TODO change this to remove assumption of unique section refs
    return clean_section_dict


"""
Generates the links for any sub-sections in the judgment. 
:param section_dict: individual dictionary for the current section 
:param match: the section reference found in the paragraph
"""


def create_sub_section_links(section_dict, match):

    new_section_dict = section_dict.copy()
    curr_href = new_section_dict['section_href']
    # get the sub-section number
    sub_section = re.findall(patterns['sub_section'], match)
    # get the number itself
    sub_section_number = get_clean_section_number(sub_section[0])
    new_href = curr_href + "/" + str(sub_section_number)
    # replace href in section_dict with new_href
    new_section_dict['section_href'] = new_href

    return new_section_dict


"""
Check if the current reference is a sub-section.
:param section: the section to check
"""


def check_if_sub_section(section):
    return re.search(patterns['sub_section'], section)


"""
Performs the check if the current reference has been redefined and returns the correct reference by using the paragraph number. 
:param section_matches: list of dictionaries that include where that section has been redefined
:param para_number: the number of the paragraph in the judgment
"""


def get_correct_section_def(section_matches, cur_para_number, cur_pos):
    pos_refs = np.asarray(
        [(match['para_number'], match['ref_position']) for match in section_matches])
    para_numbers = pos_refs[:, 0]
    idx = (np.abs(para_numbers - cur_para_number)).argmin()
    candidates = [
        match for match in section_matches if match['para_number'] == para_numbers[idx]]
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        positions = pos_refs[:, 1]
        idx = (np.abs(positions - cur_pos)).argmin()
        return [match for match in section_matches if match['ref_position'] == positions[idx]][0]
    else:
        print("ERROR: THIS SHOULDN'T HAPPEN!")

    # i = 0
    # while i < len(section_matches) - 1:
    #     # if the current para number is greater than but less than next para number, return the current match
    #     curr_match = section_matches[i]['para_number']
    #     next_match = section_matches[i+1]['para_number']
    #     if para_number > curr_match and para_number < next_match:
    #         return section_matches[i]

    #     i += 1

    # return False



"""
Matches all sections found in the judgment to the correct legislation, and provides necessary information for the replacements.
:param section_dict: master dictionary of all sections in the judgment
:param matches: list of the matches for the section references
:param para_number: current paragraph number in the judgment
"""


def provision_replacer(section_dict, matches, para_number):

    # for each section found in the paragraph
    for pos, match in matches:

        clean_section_num = get_clean_section_number(match)
        clean_section = "section " + str(clean_section_num)

        # check if we have a match for the section that we've found
        if clean_section in section_dict.keys():
            values = section_dict[clean_section]
            # if they referred to the section before it was defined in a paragraph with linked leg, skip
            if para_number < values[0]['para_number']:
                print("ERROR: THIS SHOULDN'T HAPPEN!")
                continue

            # if the section was re-defined (aka there is more than one dictionary), handle this
            if len(values) > 1:
                correct_reference = get_correct_section_def(
                    values, para_number, pos)
                # if correct_reference == False:
                #     continue

            else:
                correct_reference = values[0]

            # check if this was a sub_section - as we only initially match to sections to create master dictionary
            if check_if_sub_section(match):
                correct_reference = create_sub_section_links(
                    correct_reference, match)

            print(f"{match} \t {correct_reference['para_number']} \t {correct_reference['ref_position']} \t {correct_reference['section_href']}")
            

def main(enriched_judgment_file_path):
    for filename in os.listdir(enriched_judgment_file_path):
        enriched_judgment_file = os.path.join(
            enriched_judgment_file_path, filename)
        print(enriched_judgment_file)
        with open(enriched_judgment_file, "r") as f:
            soup = BeautifulSoup(f, 'xml')
        text = soup.find_all('p')
        cur_para_number = 0
        section_dict = {}
        for line in text:
            cur_para_number += 1
            sections = detect_reference(str(line), 'section')
            if sections:
                # if "type=\"legislation\"" in str(line): #TODO switch this to look for section first
                legislations = detect_reference(str(line))
                section_to_leg_matches = find_closest_legislation(
                    legislations, sections, THR)
                # create the master section dictionary with relevant leg links
                section_dict = save_section_to_dict(
                    section_to_leg_matches, cur_para_number, section_dict)
                provision_replacer(section_dict, sections, cur_para_number)
        # replacement logic
        # if section_dict:
        #     para_number = 0
        #     for line in text:
        #         para_number += 1
        #         # find all sections in the match, regardless of whether they are in a paragraph with a legislation or not
        #         matches = re.finditer(patterns['section'], str(line))
        #         matches_lst = [i.group(0) for i in matches]
        #         if matches_lst:
        #             provision_replacer(section_dict, matches_lst, para_number)


# main("legislation_provisions_extraction/test_judgments")
