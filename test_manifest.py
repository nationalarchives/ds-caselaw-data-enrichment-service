from cgi import test
import pandas as pd
from spacy.lang.en import English

MANIFEST = pd.read_csv("rules/2022_02_24_Citation_Manifest.csv")

nlp = English()
nlp.max_length = 1500000
patterns = MANIFEST["pattern"].tolist()

with open("test_citation_patterns.jsonl", "w+") as patterns_file:
    for pattern in patterns:
        patterns_file.write(pattern + "\n")

citation_ruler = nlp.add_pipe("entity_ruler").from_disk("test_citation_patterns.jsonl")

examples = MANIFEST["matchExample"].tolist()

MATCHED_IDS = []

for example in examples:
    doc = nlp(example)
    for token in doc:
        print (token.text)
    ent = [str(ent.ent_id_) for ent in doc.ents][0]
    print (example,ent)
    MATCHED_IDS.append(ent)
    
MATCHED_IDS = list(set(MATCHED_IDS))
print(len(MATCHED_IDS), MANIFEST.shape[0])
assert len(MATCHED_IDS) == MANIFEST.shape[0]
