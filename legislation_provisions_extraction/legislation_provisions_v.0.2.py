# from html import entities
import re, os
from bs4 import BeautifulSoup

patterns = {
    'legislation':r'<ref(.*?)type=\"legislation\"(.*?)ref>',
    'section':r'( [sS]ection\W*[0-9]+(?=)|[sS]ections\W*[0-9]+| [sS]+\W*[0-9]+)(\W*\([0-9]+\))?', 
    'sub_section': r'/\([0-9]+\)/gm' 
}

# get the href from the xml 
def get_legislation_href(tagged_legislation): 
    soup = BeautifulSoup(tagged_legislation,'xml')
    href_all = []
    for ref in soup.find_all('ref', href=True):
        href = ref['href']
        href_all.append(href)
    return href_all

def create_section_href(section, legislation_href): 
    # return this as an array where there are multiple hrefs - not currently handled
    number = re.findall(r'\d+', section)
    href = str(legislation_href[0]) +"/section/"+str(number[0])
    return href

def detect_reference(text, etype='legislation'):
    # returns a list of tuples in the form [((start, end), detected_ref)]
    references = [(m.span(), m.group()) for m in re.finditer(patterns[etype], text)]
    return references

def find_closest_legislation(legislations, sections):
    section_dict = {}
    current_match = {}

    # iterate through each of the sections found in that paragraph
    for section in sections:
        first_match = True
        section_loc = section[0]
        section_loc_average = (section_loc[0] + section_loc[1])/2

        # iterate through the legislation found in the same para to find the closest
        for legislation in legislations: 
            leg_loc = legislation[0]
            leg_loc_average = (leg_loc[0] + leg_loc[1])/2 # take the average of the start and end points
            distance = abs(leg_loc_average - section_loc_average) # get the absolute distance between the two

            # first legislation matched
            if section[1] not in current_match.keys():
                current_match[section[1]] = {'legislation': legislation[1], 'distance': distance}
            else:
                # if the distance is closer, update the legislation
                if distance < current_match[section[1]]['distance']:
                    current_match[section[1]] = {'legislation': legislation[1], 'distance': distance}
                
        section_dict[section[1]] = current_match[section[1]]['legislation']

    return section_dict

def generate_sub_section_links(section_dict): 
    # we generate sub-section links here
    a = 1


def get_clean_section_number(section):
    section_number = re.findall(r'\d+', section)
    return section_number[0]

def save_section_to_dict(section_dict, para_number, clean_section_dict): 

    for section in section_dict: 
        section_number = get_clean_section_number(section)
        full_ref = section_dict[section]
        soup = BeautifulSoup(full_ref,'xml')
        ref = soup.find('ref') 
        leg_href = ref['href']
        section_href = str(leg_href) +"/section/"+str(section_number)
        canonical = ref.find('canonical')
        clean_section = "section " + str(section_number)

        if clean_section not in clean_section_dict.keys():
            clean_section_dict[clean_section] = [{'para_number': para_number, 'ref': ref, 'leg_href': leg_href, 'canonical': canonical, 'section_href': section_href}]

        else:
            value = clean_section_dict[clean_section]
            new_value = [value, {'para_number': para_number, 'ref': ref, 'leg_href': leg_href, 'canonical': canonical, 'section_href': section_href}]
            clean_section_dict[clean_section] = new_value
      
    return clean_section_dict

def provision_replacer(text, section_dict):


    return

def main(enriched_judgment_file_path): 
    for filename in os.listdir(enriched_judgment_file_path):
        enriched_judgment_file = os.path.join(enriched_judgment_file_path, filename)
        print(enriched_judgment_file)
        with open(enriched_judgment_file, "r") as f:
            soup = BeautifulSoup(f,'xml')
        text = soup.find_all('p') 
        para_number = 0
        section_dict = {}
        for line in text: 
            para_number += 1
            if "type=\"legislation\"" in str(line):
                legislations = detect_reference(str(line))
                sections = detect_reference(str(line), 'section')
                section_to_leg_matches = find_closest_legislation(legislations, sections)
                # create the master section dictionary 
                section_dict = save_section_to_dict(section_to_leg_matches, para_number, section_dict)
                print(section_dict)











        #         if sections and len(split_sentences) > 1:
                #TODO: rewrite this according to how resolve_section_to_leg is implemented
        #         for section in section_to_leg:
        #             href = get_legislation_href(split_sentences) # update this to handle multiple refs in one line
        #             section_href = create_section_href(section, href) 
        #             new_section_dict = add_section_to_dict(section_dict, line_number, section, section_href) # maintaining the line number for the replacements
        #             section_dict.update(new_section_dict)
        # for k, v in section_dict.items():
        #     print(k, v)
        # print("\n")


main("legislation_provisions_extraction/test_judgments")

# TODO: 
# - add support for sections referenced w/o legislation 
# - switch to dictionary - looking at orphan provisions]

