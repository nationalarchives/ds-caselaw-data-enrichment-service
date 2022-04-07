import spacy
from abbreviations import AbbreviationDetector
from spacy.language import Language

def abb_pipeline(judgment_content_text):
    nlp = spacy.load("en_core_web_sm", exclude=['tok2vec', 'attribute_ruler', 'lemmatizer', 'ner'])

    # init the class - stateful pipeline component 
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(nlp, name: str): 
        return AbbreviationDetector(nlp)

    nlp.add_pipe("abbreviation_detector") 

    doc = nlp(judgment_content_text)

    REPLACEMENTS_ABBR = []
    for abrv in doc._.abbreviations:
        abr_tuple = (str(abrv), str(abrv._.long_form))
        REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
    
