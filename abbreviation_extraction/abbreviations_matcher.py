"""
Main file that controls the abbreviation detection, including the creation of the 
AbbreviationDetector class and the pipeline. 
"""


from collections import namedtuple
import spacy
from spacy.language import Language
import sys 
sys.path.append("./")
from abbreviation_extraction.abbreviations import AbbreviationDetector

abb = namedtuple('abb', 'abb_match longform')

def split_list(a, n):
    """
    Function to split the content into list of chunks of size n
    :param a: list of words
    :param n: size of the chunks
    """
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def abb_pipeline(judgment_content_text, nlp):
    """
    Main controller of the abbreviation detection pipeline. 
    :param judgment_content_text: judgment content
    :param nlp: previously created spaCy nlp component
    """
    # init the class - stateful pipeline component 
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(nlp, name: str): 
        return AbbreviationDetector(nlp)

    nlp.add_pipe("abbreviation_detector", last=True)
    print("added abbr pipeline")

    REPLACEMENTS_ABBR = []

    # Randomly split the judgment text into 5 chunks to avoid memory issues
    judgment_content_text_list = judgment_content_text.split(' ')
    judgment_chunks = list(split_list(judgment_content_text_list, 5))
    
    for chunk in judgment_chunks:
        chunk = " ".join(chunk)
        doc = nlp(chunk)
        for abrv in doc._.abbreviations:
            abr_tuple = abb(str(abrv), str(abrv._.long_form))
            REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
