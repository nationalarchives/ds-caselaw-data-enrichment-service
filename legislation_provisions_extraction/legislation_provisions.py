import re
from bs4 import BeautifulSoup
import os


def get_section(line):
    split_lines = re.split(r'<ref canon', line)
    clean_sent = []

    # TODO - cleaner way of keeping the tag in bc regex split above removes it
    for sent in split_lines: 
        if "ical=" in sent: 
            sent = "<ref canon" + sent
        clean_sent.append(sent)

    sections = []
    # only currently looking at the sentence before the legislation
    if  "<ref canon" not in clean_sent[0]:
        # need to check for leading whitespace to avoid catching plural + a year
        sections = re.findall(r' [sS]ections.[0-9]+\([0-9]+\)| [sS]ection.[0-9]+\([0-9]+\)| [sS] .[0-9]+\([0-9]+\)| [sS].[0-9]+.\([0-9]+\)| [sS].[0-9]+\([0-9]+\)| [sS]ection.[0-9]+| [sS].[0-9]+| [sS]ections.[0-9]+| [sS] .[0-9]+| [sS]. [0-9]+', clean_sent[0])

    # strip leading whitespace - needs to be kept in to stop quirks from slipping through 
    sections_clean = []
    for section in sections: 
        sections_clean.append(section.lstrip(' '))

    return sections_clean, clean_sent

# get the href from the xml 
def get_legislation_href(split_sentences): 
    soup = BeautifulSoup(split_sentences[1],'xml')
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
    
def add_section_to_dict(section_dict, line_number, section, legislation_href):
        # clean the section to just be the section with number to avoid duplicates
    section_with_number = re.findall(r'\d+', section)
    clean_section = "section " + section_with_number[0]
    new_item = {'line_number': line_number, 'legislation_href': legislation_href}

    # this cleans it up for where the same section has been defined before, and adds it as a value to the existing key rather than overwriting it
    if clean_section in section_dict: 
        references = section_dict[clean_section]
        if new_item not in references:
            references.append(new_item)
            section_dict[clean_section] = references
    else: 
        list = [new_item]
        section_dict[clean_section] = list
    
    return section_dict

def main(enriched_judgment_file_path): 
    for filename in os.listdir(enriched_judgment_file_path):
        enriched_judgment_file = os.path.join(enriched_judgment_file_path, filename)
        with open(enriched_judgment_file, "r") as f:
            section_dict = {}
            line_number = 0 # use the line number to avoid duplicate sections being identified
            soup = BeautifulSoup(f,'xml')
            text = soup.find_all('p')
            for line in text:
                line_number += 1
                if "type=\"legislation\"" in str(line):
                    sections, split_sentences = get_section(str(line))
                    # length of the split sentences needs to be greater to ensure it was successfully split - accounting for the different examples in our current test judgments
                    if sections and len(split_sentences) > 1:
                        for section in sections:
                            href = get_legislation_href(split_sentences) # update this to handle multiple refs in one line
                            section_href = create_section_href(section, href) 
                            new_section_dict = add_section_to_dict(section_dict, line_number, section, section_href) # maintaining the line number for the replacements
                            section_dict.update(new_section_dict)
            for k, v in section_dict.items():
                print(k, v)
            print("\n")


main("/Users/amy.conroy/Documents/Development/project_TNA/legislation_provisions_extraction/test_judgments/")

"""
TODO: 
- test with "sections 12 - 13" or "sections 12 and 13"
- add the replacer logic (seperately)
- test with multiple pieces of leg in the same sentence
    - handle multiple sections mentioned in one sentence
- add regex to a module
- handle articles / clause / regulation / rule / part
"""
