# from html import entities
import re, os
from bs4 import BeautifulSoup

patterns = {
    'legislation':r'<ref(.*?)type=\"legislation\"(.*?)ref>',
    'section':r'( [sS]ection\W*[0-9]+(?=)|[sS]ections\W*[0-9]+| [sS]+\W*[0-9]+)(\W*\([0-9]+\))?', 
    'sub_section': r'\([0-9]+\)' 
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

        new_definition = {'para_number': para_number, 'ref': ref, 'leg_href': leg_href, 'canonical': canonical, 'section_href': section_href}

        if clean_section not in clean_section_dict.keys():
            clean_section_dict[clean_section] = [new_definition]

        else:
            value = clean_section_dict[clean_section]
            value.append(new_definition)
            clean_section_dict[clean_section] = value

    
    return clean_section_dict

def create_sub_section_links(section_dict, match): 

    new_section_dict = section_dict.copy()
    curr_href = new_section_dict['section_href']
    sub_section = re.findall(patterns['sub_section'], match)
    sub_section_number = get_clean_section_number(sub_section[0])
    new_href = curr_href + "/" + str(sub_section_number)
    # replace href in section_dict with new_href
    new_section_dict['section_href'] = new_href

    return new_section_dict

def check_if_sub_section(section):
    if re.search(patterns['sub_section'], section):
        return True
    else:
        return False

def create_replacement_dictionary(section_dict, para_number, match, sub_section, clean_section):
    return 

def get_correct_section_def(section_matches, para_number): 

    i = 0
    while i < len(section_matches) - 1:
        # if the current para number is greater than but less than next para number, return the current match
        curr_match = section_matches[i]['para_number']
        next_match = section_matches[i+1]['para_number']
        if para_number > curr_match and para_number < next_match:
            return section_matches[i]
        
        i += 1

    return False

def provision_replacer(text, section_dict, matches, para_number):

    for match in matches:

        clean_section_num = get_clean_section_number(match)
        clean_section = "section " + str(clean_section_num)
        if clean_section in section_dict.keys():
            values = section_dict[clean_section]
            # if they referred to the section before it was defined in a paragraph with linked leg, skip
            if para_number < values[0]['para_number']:
                continue
            
            # if the section was re-defined, handle this
            if len(values) > 1: 
                correct_reference = get_correct_section_def(values, para_number)
                if correct_reference == False: 
                    continue
            
            else: 
                correct_reference = values[0]
            
            # check if this was a sub_section 
            sub_section = check_if_sub_section(match)
            if sub_section:
                correct_reference = create_sub_section_links(correct_reference, match)
            print(match)
            print(correct_reference)




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
                # create the master section dictionary with relevant leg links
                section_dict = save_section_to_dict(section_to_leg_matches, para_number, section_dict)
                
                
        # replacement logic
        if section_dict:
            para_number = 0
            for line in text:
                para_number += 1
                matches = re.finditer(patterns['section'], str(line))
                matches_lst = [i.group(0) for i in matches]
                if matches_lst:
                    provision_replacer(text, section_dict, matches_lst, para_number)




main("legislation_provisions_extraction/test_judgments")

