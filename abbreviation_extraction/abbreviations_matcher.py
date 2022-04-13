from collections import namedtuple
import spacy
from spacy.language import Language
from abbreviation_extraction.abbreviations import AbbreviationDetector

abb = namedtuple('abb', 'abb_match longform')

def abb_pipeline(judgment_content_text, nlp):
    # init the class - stateful pipeline component 
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(nlp, name: str): 
        return AbbreviationDetector(nlp)

    nlp.add_pipe("abbreviation_detector") 

    doc = nlp(judgment_content_text)

    REPLACEMENTS_ABBR = []
    for abrv in doc._.abbreviations:
        abr_tuple = abb(str(abrv), str(abrv._.long_form))
        REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
    
