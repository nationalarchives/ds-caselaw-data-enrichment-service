import os
import json

import spacy

from utils.helper import parse_file, load_patterns
from database.db_connection import create_connection, close_connection, get_legtitles
from replacer.replacer import replacer_pipeline, write_replacements_file
from caselaw_extraction.caselaw_matcher import case_pipeline
from legislation_processing.legislation_matcher_hybrid import leg_pipeline
from abbreviation_extraction.abbreviations_matcher import abb_pipeline

ROOTDIR = "2020"
db_conn = create_connection('tna', 'editha.nemsic', 'localhost', 5432)
leg_titles = get_legtitles(db_conn)
load_patterns(db_conn)

nlp = spacy.load("en_core_web_sm", exclude=['tok2vec', 'attribute_ruler', 'lemmatizer', 'ner'])
nlp.max_length = 2500000

citation_ruler = nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

tuple_file = open("tuples.jsonl", "w+")

for subdir, dirs, files in os.walk(ROOTDIR):
  for file in files[:2]:
    if not file.startswith('.'):
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
      # print(test_caselaw_file)
      # write_replacements_file(REPLACEMENTS_LEG)
      # write_replacements_file(REPLACEMENTS_ABBR)
  
      # Writing to sample.json
      tuple_file.write(test_caselaw_file)
      tuple_file.write(test_leg_file)
      tuple_file.write(test_abb_file)

      # replacements = []
      # replacement_tuples_case = []
      # replacement_tuples_leg = []
      # replacement_tuples_abb = []
      # tuple_file = open("tuples.jsonl", "r")

      # for line in tuple_file:
      #     replacements.append(json.loads(line))

      # for i in replacements:
      #     key, value = list(i.items())[0]
      #     if key == 'case':
      #         case_law_tuple = tuple(i['case'])
      #         replacement_tuples_case.append(case_law_tuple)
      #     elif key == 'leg':
      #         leg_tuple = tuple(i['leg'])
      #         replacement_tuples_leg.append(leg_tuple)
      #     else:
      #         abb_tuple = tuple(i['abb'])
      #         replacement_tuples_abb.append(abb_tuple)

      # file_data_enriched = replacer_pipeline(file_data, replacement_tuples_case, replacement_tuples_leg, replacement_tuples_abb)
      file_data_enriched = replacer_pipeline(file_data, REPLACEMENTS_CASELAW, REPLACEMENTS_LEG, REPLACEMENTS_ABBR)

      output_file = f"output/{file}".replace(".xml", "_enriched.xml")

      with open(output_file, "w") as data_out:
          data_out.write(file_data_enriched)

close_connection(db_conn)