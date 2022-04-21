from collections import namedtuple
import spacy
from spacy.language import Language
from abbreviation_extraction.abbreviations import AbbreviationDetector

abb = namedtuple('abb', 'abb_match longform')

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def abb_pipeline(judgment_content_text, nlp):
    # init the class - stateful pipeline component 
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(nlp, name: str): 
        return AbbreviationDetector(nlp)

    nlp.add_pipe("abbreviation_detector", last=True)
    print("added abbr pipeline")

    REPLACEMENTS_ABBR = []

    judgment_content_text_list = judgment_content_text.split(' ')
    
    judgment_chunks = chunks(judgment_content_text_list, 5)
    for chunk in judgment_chunks:
        chunk = " ".join(chunk)
        doc = nlp(chunk)

        for abrv in doc._.abbreviations:
            abr_tuple = abb(str(abrv), str(abrv._.long_form))
            REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
    
