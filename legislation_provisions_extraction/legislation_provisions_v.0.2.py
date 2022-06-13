# from html import entities
import re, os
from bs4 import BeautifulSoup

patterns = {
    'legislation':r'<ref(.*?)type=\"legislation\"(.*?)ref>',
    'section':r'( [sS]ection\W*[0-9]+(?=)|[sS]ections\W*[0-9]+| [sS]+\W*[0-9]+)(\W*\([0-9]+\))?'
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

def resolve_section_to_leg(legislations, sections):
    # resolve explicit references - references abbreviated eg. section 13 of act (section 13) ??? <- can this occur? [AC - No, have never seen that]
    # resolve explicit references - closest to a legislation tag within a threshold eg. s.4 of act blah | act blah section 3
    # resolve other references - either by closest legislation or explicit ref. eg. section.3 of act ...<p> ...section.3 ...
    section_dict = {}
    return section_dict

def provision_replacer():
    # split body at [start] point of detected sections 

    #make replacement per split then join

    return

def main(enriched_judgment_file_path): 
    for filename in os.listdir(enriched_judgment_file_path):
        enriched_judgment_file = os.path.join(enriched_judgment_file_path, filename)
        print(enriched_judgment_file)
        with open(enriched_judgment_file, "r") as f:
            soup = BeautifulSoup(f,'xml')
        text = soup.find_all('p') #TODO: decide whether to resolve per <p> or per body. Cur.Pref=body
        for line in text: 
            if "type=\"legislation\"" in str(line):
                legislations = detect_reference(str(line))
                print(legislations)
                sections = detect_reference(str(line), 'section')
                print(sections)
                section_to_leg = resolve_section_to_leg(legislations, sections)
                
                # save the sections that are already resolved as well - then replace if that section already exists 

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

