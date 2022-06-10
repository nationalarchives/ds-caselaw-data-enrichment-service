import pandas as pd
import spacy

"""
Test for the rules manifest. 
"""

MANIFEST = pd.read_csv("caselaw_extraction/rules/2022_04_05_Citation_Manifest.csv")

nlp = spacy.load("en_core_web_sm", exclude=['tok2vec', 'attribute_ruler', 'lemmatizer', 'ner'])
nlp.max_length = 2500000
patterns = MANIFEST["pattern"].tolist()

with open("tests/test_citation_patterns.jsonl", "w+") as patterns_file:
    for pattern in patterns:
        patterns_file.write(pattern + "\n")

citation_ruler = nlp.add_pipe("entity_ruler").from_disk("test_citation_patterns.jsonl")

examples = MANIFEST["matchExample"].tolist()

MATCHED_IDS = []

for example in examples:
    doc = nlp(example)
    ent = [str(ent.ent_id_) for ent in doc.ents][0]
    print(example, ent)
    MATCHED_IDS.append(ent)

MATCHED_IDS = list(set(MATCHED_IDS))
print(len(MATCHED_IDS), MANIFEST.shape[0])
assert len(MATCHED_IDS) == MANIFEST.shape[0]
