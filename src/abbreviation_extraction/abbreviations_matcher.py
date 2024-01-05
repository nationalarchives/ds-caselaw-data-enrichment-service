"""
Main file that controls the abbreviation detection, including the creation of the
AbbreviationDetector class and the pipeline.
"""


from collections import namedtuple

import spacy
from spacy.language import Language

from abbreviation_extraction.abbreviations import AbbreviationDetector

abb = namedtuple("abb", "abb_match longform")


def chunking_mechanism(docobj, n, start, end):
    """
    Function to split the content into a list of chunks of size n,
    taking into account the start and end position of abbreviations.
    :param docobj: Doc object of the judgement content created in abb_pipeline
    :param n: size of the chunks
    :param start: starting position of detected abbreviation
    :param end: ending position of detected abbreviation

    Returns
    -------
    List: Judgment split into chunks
    """
    k, m = divmod(len(docobj), n)
    pos = [[i * k + min(i, m), (i + 1) * k + min(i + 1, m)] for i in range(n)]
    # If the abbreviation will be cut in two by the above split, adjust where
    # the list is split
    for p in range(len(pos)):
        if start < pos[p][1] and end > pos[p][1]:
            pos[p][1] = end
            pos[p + 1][0] = end
        else:
            continue
    judgment_chunks = [docobj[split[0] : split[1]] for split in pos]
    return judgment_chunks


def abb_pipeline(judgment_content_text: str, nlp: spacy.lang.en.English) -> list[abb]:
    """
    Main controller of the abbreviation detection pipeline.
    :param judgment_content_text: judgment content
    :param nlp: previously created spaCy nlp component

    Returns
    -------
    List[Tuple[Str, Str]]: abbreviation and abbreviation long form
    """

    # init the class - stateful pipeline component
    @Language.factory("abbreviation_detector")
    def create_abbreviation_detector(
        nlp: spacy.lang.en.English, name: str
    ) -> AbbreviationDetector:
        return AbbreviationDetector(nlp)

    nlp.add_pipe("abbreviation_detector", last=True)
    print("added abbr pipeline")

    REPLACEMENTS_ABBR = []

    # new chunking mechanism
    docobj = nlp(judgment_content_text)
    judgment_chunks = chunking_mechanism(docobj, 5, 79, 83)
    chunk_strings = [chunk.text for chunk in judgment_chunks]

    # replace abbreviations in each chunk
    for chunk in chunk_strings:
        doc = nlp(chunk)
        for abrv in doc._.abbreviations:
            abr_tuple = abb(str(abrv), str(abrv._.long_form))
            REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
