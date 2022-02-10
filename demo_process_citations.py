import re

import pandas as pd
from spacy.lang.en import English

from utils.demo_text import test_string

# TODO: move me into my own module
def apply_correction_strategy(citation_type, citation_match, canonical_form):
    """Find the appropriate correction strategy and apply it"""

    # e.g [2022] EWCA Civ 123
    if citation_type == "NCitYearAbbrNum":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        num = components[1]
        corrected_citation = canonical_form.replace("dddd", year).replace("d+", num)
    
    # e.g. [2022] EWHC 123 (Admin)
    # there's an argument for merging this with the NCitYearAbbrNum strategy
    elif citation_type == "NCitYearAbbrNumDiv":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        num = components[1]
        corrected_citation = canonical_form.replace("dddd", year).replace("d+", num)

    # e.g. [2022] UKFTT 2020_0341 (GRC)
    elif citation_type == "NCitYearAbbrNumUnderNumDiv":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        first_num = components[1]
        second_num = components[2]
        corrected_citation = canonical_form.replace("dddd", year).replace("d1", first_num).replace("d2", second_num)

    # e.g. [2022] UKET 123456/2022
    elif citation_type == "NCitYearAbrrNumStrokeNum":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        first_num = components[1]
        second_num = components[2]
        corrected_citation = canonical_form.replace("dddd", year).replace("d1", first_num).replace("d2", second_num)

    return corrected_citation

def check_if_canonical(rule_id_):
    """Check if the matched citation is well-formed"""
    matched_rule = rules_manifest.loc[rules_manifest["id"] == rule_id_]
    is_canonical = matched_rule["isCanonical"].iloc[0]
    return is_canonical

def correct_malformed_citation(rule_id_, citation_match):
    """Correct the format of a malformed citation"""
    matched_rule = rules_manifest.loc[rules_manifest["id"] == rule_id_]
    citation_type = matched_rule["citationType"].iloc[0]
    canonical_form = matched_rule["canonicalForm"].iloc[0]
    return apply_correction_strategy(citation_type, citation_match, canonical_form)


rules_manifest = pd.read_csv("2022_02_08_Citation_Manifest.csv")
patterns = rules_manifest["pattern"].tolist()
with open("citation_patterns_test2.jsonl", "w+") as patterns_file:
    for pattern in patterns:
        patterns_file.write(pattern + "\n")

nlp = English()
nlp.max_length = 1500000
citation_ruler = nlp.add_pipe("entity_ruler").from_disk("citation_patterns_test2.jsonl")

doc = nlp(test_string)
for ent in doc.ents:
    rule_id_ = ent.ent_id_
    citation_match = ent.text
    print(rule_id_, citation_match)
    if check_if_canonical(rule_id_) == False:
        corrected_citation = correct_malformed_citation(rule_id_, citation_match)
        print ("CORRECTED:", corrected_citation)
    else:
        pass

