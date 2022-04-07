import re
from database.db_connection import get_matched_rule
from caselaw_extraction.correction_strategies import apply_correction_strategy

def create_URI(uri_template, year, d1, d2):
    if 'd1' in str(uri_template):
        URI = uri_template.replace('year', year).replace('d1', d1)
    elif 'd2' in str(uri_template):
        URI = uri_template.replace('year', year).replace('d1', d1).replace('d2', d2)
    else:
        URI = uri_template
    return URI

def case_pipeline(doc, db_conn):

    REPLACEMENTS_CASELAW = []

    for ent in doc.ents:
        rule_id = ent.ent_id_
        citation_match = ent.text
        family, URItemplate, is_neutral, is_canonical, citation_type, canonical_form = get_matched_rule(db_conn, rule_id)
        if is_canonical == False:
            corrected_citation, year, d1, d2 = apply_correction_strategy(citation_type, citation_match, canonical_form)
            print ("-----> CORRECTED:", corrected_citation)
            if URItemplate != None:
                URI = create_URI(URItemplate, year, d1, d2)
            else:
                URI = '#'
            replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        else:
            components = re.findall(r"\d+", citation_match)
            if 'Year' in citation_type:
                year = components[0]
                d1 = components[1]
                if len(components) > 2:
                    d2 = components[2]
                else:
                    d2 = ''
            else: 
                year = 'No Year'
                d1 = components[0]
                if len(components) > 1:
                    d2 = components[1]
                else:
                    d2 = ''
            if URItemplate != None:
                URI = create_URI(URItemplate, year, d1, d2)
            else:
                URI = '#'
            replacement_entry = (citation_match, citation_match, year, URI, is_neutral)
        
        REPLACEMENTS_CASELAW.append(replacement_entry)
    
    return REPLACEMENTS_CASELAW