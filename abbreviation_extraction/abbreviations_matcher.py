from collections import namedtuple

abb = namedtuple('abb', 'abb_match longform')

def abb_pipeline(doc):
    REPLACEMENTS_ABBR = []
    for abrv in doc._.abbreviations:
        abr_tuple = abb(str(abrv), str(abrv._.long_form))
        REPLACEMENTS_ABBR.append(abr_tuple)

    return REPLACEMENTS_ABBR
    
