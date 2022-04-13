from collections import namedtuple
import spacy
from spacy.language import Language

abb = namedtuple('abb', 'abb_match longform')

def abb_pipeline(file_content, nlp):
    from abbreviation_extraction.abbreviations import AbbreviationDetector

    # init the class - stateful pipeline component 
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(nlp, name: str): 
        return AbbreviationDetector(nlp)

    nlp = spacy.blank("en")
    nlp.add_pipe("abbreviation_detector") 

    doc = nlp(file_content)

    REPLACEMENTS_ABBR = []
    for abrv in doc._.abbreviations:
        print(abrv)
        abr_tuple = abb(str(abrv), str(abrv._.long_form))
        REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
    
