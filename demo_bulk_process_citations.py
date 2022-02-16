import os
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

from spacy.lang.en import English
import bs4 as BeautifulSoup

from utils.demo_text import test_string
from rules.correction_strategies import apply_correction_strategy

#TODO: capture year from well-formed references that include years

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

def load_manifest():
    """Load the rules manifest and patterns file"""
    rules_manifest = pd.read_csv("rules/2022_02_16_Citation_Manifest.csv")
    patterns = rules_manifest["pattern"].tolist()
    with open("rules/citation_patterns.jsonl", "w+") as patterns_file:
        for pattern in patterns:
            patterns_file.write(pattern + "\n")
    return rules_manifest

def get_matched_rule_name(rule_id_):
    """Get the rule name for a given rule_id_"""
    matched_rule = rules_manifest.loc[rules_manifest["id"] == rule_id_]
    return matched_rule["description"].iloc[0]

def analyse_matched_ids(MATCHED_RULE_ID):
    """Do basic analysis on matched rules"""
    rule_match_counts = Counter(MATCHED_RULE_ID)
    df = pd.DataFrame.from_dict(rule_match_counts, orient="index").reset_index()
    RULE_NAMES = [get_matched_rule_name(id) for id in df["index"]]
    df["rule_name"] = RULE_NAMES
    df = df.sort_values(by=0)
    df.to_csv("matched_rules.csv", index=True)
    df.plot(x="rule_name", y=0, kind="barh", figsize=(20,20), legend=False, color="black")
    plt.savefig("plots/matched_rules.png")

def replacer(file_data, replacement):
    """Do a basic replacement in the XML"""
    replacement_string = f'<ref type="case" canonical_form="{replacement[1]}">{replacement[0]}</ref>'
    file_data = str(file_data).replace(replacement[0], replacement_string)
    return file_data


ROOTDIR = "tna-backcatalogue/ewca/civ/2020"
rules_manifest = load_manifest()
nlp = English()
nlp.max_length = 1500000
citation_ruler = nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

MATCHED_RULE_ID = []

for subdir, dirs, files in os.walk(ROOTDIR):
    for file in files[:100]:
        REPLACEMENTS = []
        file_path = os.path.join(subdir, file)
        with open(file_path, "r", encoding="utf-8") as file_in:
            print(file)
            file_data = file_in.read()
            soup = BeautifulSoup.BeautifulSoup(str(file_data), "lxml")
            judgment_content = soup.find_all("content")
            judgment_content_text = " ".join([content.text for content in judgment_content])
            doc = nlp(judgment_content_text)
            for ent in doc.ents:
                rule_id_ = ent.ent_id_
                citation_match = ent.text
                MATCHED_RULE_ID.append(rule_id_)
                if check_if_canonical(rule_id_) == False:
                    corrected_citation = correct_malformed_citation(rule_id_, citation_match)
                    print ("-----> CORRECTED:", corrected_citation, file)
                    replacement_entry = (citation_match, corrected_citation)
                else:
                    replacement_entry = (citation_match, citation_match)
                REPLACEMENTS.append(replacement_entry)
        
        for replacement in REPLACEMENTS:
            file_data = replacer(file_data, replacement)
        
        output_file = f"output/{file}".replace(".xml", "_enriched.xml")

        with open(output_file, "w") as data_out:
            data_out.write(file_data)


analyse_matched_ids(MATCHED_RULE_ID)

