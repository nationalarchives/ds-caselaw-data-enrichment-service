import json
import os

import spacy

from abbreviation_extraction.abbreviations_matcher import abb_pipeline
from caselaw_extraction.caselaw_matcher import case_pipeline
from database.db_connection import (
    close_connection,
    create_connection,
    get_legtitles,
)
from legislation_extraction.legislation_matcher_hybrid import leg_pipeline
from replacer.replacer import replacer_pipeline, write_replacements_file
from utils.helper import load_patterns, parse_file

ROOTDIR = "2020"
db_conn = create_connection("tna", "editha.nemsic", "localhost", 5432)
leg_titles = get_legtitles(db_conn)
load_patterns(db_conn)

nlp = spacy.load(
    "en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"]
)
nlp.max_length = 2500000

citation_ruler = nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

tuple_file = open("tuples.jsonl", "w+")

for subdir, dirs, files in os.walk(ROOTDIR):
    for file in files[:2]:
        if not file.startswith("."):
            file_path = os.path.join(subdir, file)
            with open(file_path, "r", encoding="utf-8") as file_in:
                print(file)
                file_data = file_in.read()
                judgment_content_text = parse_file(file_data)
                doc = nlp(judgment_content_text)

            # create replacements for case law, legislation and abbreviations
            REPLACEMENTS_CASELAW = case_pipeline(doc, db_conn)
            REPLACEMENTS_LEG = leg_pipeline(leg_titles, nlp, doc, db_conn)
            REPLACEMENTS_ABBR = abb_pipeline(judgment_content_text)

            test_caselaw_file = write_replacements_file(REPLACEMENTS_CASELAW)
            test_leg_file = write_replacements_file(REPLACEMENTS_LEG)
            test_abb_file = write_replacements_file(REPLACEMENTS_ABBR)

            # Writing to sample.json
            tuple_file.write(test_caselaw_file)
            tuple_file.write(test_leg_file)
            tuple_file.write(test_abb_file)

            file_data_enriched = replacer_pipeline(
                file_data, REPLACEMENTS_CASELAW, REPLACEMENTS_LEG, REPLACEMENTS_ABBR
            )

            output_file = f"output/{file}".replace(".xml", "_enriched.xml")

            with open(output_file, "w") as data_out:
                data_out.write(file_data_enriched)

close_connection(db_conn)
