"""
@author: editha.nemsic
This code builds the Case Law Annotator. The 3 main functionalities are: 

1. Detect references to well-formed (canonical) citations and malformed citations
2. Correct malformed citations to their canonical form
3. Mark up the detected citations in the LegalDocML

- The input to case_pipeline is a spacy Doc object. 
- The first step is to detect the entities based on the EntityRuler built into the nlp pipeline in a previous step.
- Once the citation match and its corresponding ID have been detected, the code queries a 'Rules Manifest' in Postgres 
to retrieve associated metadata about the matched citation.
- If the citation is well-formed, the pipeline retrieves additional metadata from the citation match, creates the corresponding URI 
and finally creates a replacement entry as a tuple.
- If the citation match is malformed, the citation match and parts of the metadata are passed to a correction pipeline before following
the same path as well-formed citation matches.
- case_pipeline returns a list of tuples that hold the replacements. 

"""

import re
from collections import namedtuple

from caselaw_extraction.correction_strategies import apply_correction_strategy
from database.db_connection import get_matched_rule

case = namedtuple("case", "citation_match corrected_citation year URI is_neutral")


def create_URI(uri_template, year, d1, d2):
    """
    Create URI.
    :param uri_template: URI template to build correct URI for detected citation
    :param year: year detected in citation
    :param d1: first digit detected in citation
    :param d2: second (optional) digit detected in citation
    :returns: URI
    """
    if "d1" in str(uri_template):
        URI = uri_template.replace("year", year).replace("d1", d1)
    elif "d2" in str(uri_template):
        URI = uri_template.replace("year", year).replace("d1", d1).replace("d2", d2)
    else:
        URI = uri_template
    return URI


def case_pipeline(doc, db_conn):

    """
    Loop through detected caselaw citations and build components for xref attribute.
    :param doc: judgment as spacy Doc object
    :param db_conn: DB connection parameters to call Rules Manifest
    :returns: list of tuples containing detected caselaw and associated attributes
    """

    REPLACEMENTS_CASELAW = []

    for ent in doc.ents:
        rule_id = ent.ent_id_
        citation_match = ent.text
        (
            family,
            URItemplate,
            is_neutral,
            is_canonical,
            citation_type,
            canonical_form,
        ) = get_matched_rule(db_conn, rule_id)
        if is_canonical == False:
            corrected_citation, year, d1, d2 = apply_correction_strategy(
                citation_type, citation_match, canonical_form
            )
            if URItemplate != None:
                URI = create_URI(URItemplate, year, d1, d2)
            else:
                URI = "#"
            replacement_entry = case(
                citation_match, corrected_citation, year, URI, is_neutral
            )
        else:
            components = re.findall(r"\d+", citation_match)
            if "Year" in citation_type:
                year = components[0]
                d1 = components[1]
                if len(components) > 2:
                    d2 = components[2]
                else:
                    d2 = ""
            else:
                year = "No Year"
                d1 = components[0]
                if len(components) > 1:
                    d2 = components[1]
                else:
                    d2 = ""
            if URItemplate != None:
                URI = create_URI(URItemplate, year, d1, d2)
            else:
                URI = "#"
            replacement_entry = case(
                citation_match, citation_match, year, URI, is_neutral
            )

        REPLACEMENTS_CASELAW.append(replacement_entry)

    return REPLACEMENTS_CASELAW
