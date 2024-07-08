import csv
import json
from pathlib import Path

from spacy.lang.en import English

"""Validates that the Citation Manifest correctly matches the Match Example to the row of the database"""

CSV_PATH = Path("src/caselaw_extraction/rules/2022_06_30_Citation_Manifest.csv")


def setup_nlp(patterns):
    nlp = English()
    ruler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns(patterns)
    return nlp


def run_nlp(nlp, text):
    doc = nlp(text)
    return [(ent.text, ent.id_) for ent in doc.ents]


def csv_as_dict(csv_path):
    with open(csv_path) as csv_file:
        csvreader = csv.reader(csv_file)
        headers = next(csvreader)
        return [{k: v for (k, v) in zip(headers, row, strict=False)} for row in csvreader]


def get_patterns(csv_dict):
    pattern_strings = [x["pattern"] for x in csv_dict]
    return [json.loads(pattern_string) for pattern_string in pattern_strings]


csv_dict = csv_as_dict(CSV_PATH)
patterns = get_patterns(csv_dict)
nlp = setup_nlp(patterns)

run_nlp(nlp, "this is [2023] UKSC 3 you know")

for item in csv_dict:
    match = run_nlp(nlp, f"jam {item['match_example']} cake")
    if not match[0][0] == item["match_example"]:
        raise RuntimeError(f"Matched {match[0][0]!r} which isn't {item['match_example']!r}")
    if not match[0][1] == item["id"]:
        raise RuntimeError(f"Matched ID was {match[0][1]!r} which isn't {item['id']!r}")
    if len(match) > 1:
        raise RuntimeError(f"{len(match)} matches for {item['match_example']!r}")
