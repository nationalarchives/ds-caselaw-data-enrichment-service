import os
import re
import pandas as pd
from collections import Counter
import json
import bs4 as BeautifulSoup

import spacy
from spacy.lang.en import English
from spacy.language import Language
from abbreviations import AbbreviationDetector

from helper import parse_file, load_patterns
from db_connection import create_connection, close_connection, get_matched_rule, get_legtitles
from correction_strategies import apply_correction_strategy
from replacer import replacer_caselaw, replacer_abbr, replacer_leg
from legislation_matcher_hybrid import leg_pipeline

ROOTDIR = "../2020"
DATABASE = "tna.db"
db_conn = create_connection(DATABASE)
leg_titles = get_legtitles(db_conn)
load_patterns(db_conn)

nlp = spacy.load("en_core_web_sm", exclude=['tok2vec', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'ner'])
nlp.max_length = 2500000

# init the class - stateful pipeline component 
@Language.factory("abbreviation_detector")
def create_abbreviation_detector(nlp, name: str): 
	return AbbreviationDetector(nlp)

citation_ruler = nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")
abbreviation_matcher = nlp.add_pipe("abbreviation_detector") 

for subdir, dirs, files in os.walk(ROOTDIR):
  # TODO: This needs to be updated to just handle the file that is being passed to it
  for file in files[:5]:
    if not file.startswith('.'):
      REPLACEMENTS_CASELAW = []
      REPLACEMENTS_ABBR = []
      file_path = os.path.join(subdir, file)
      with open(file_path, "r", encoding="utf-8") as file_in:
        print(file)
        file_data = file_in.read()
        judgment_content_text = parse_file(file_data)
        doc = nlp(judgment_content_text)
        for ent in doc.ents:
          rule_id = ent.ent_id_
          citation_match = ent.text
          is_neutral, is_canonical, citation_type, canonical_form, description = get_matched_rule(db_conn, rule_id)
          if is_canonical == False:
            corrected_citation, year = apply_correction_strategy(citation_type, citation_match, canonical_form)
            print ("-----> CORRECTED:", corrected_citation, file)
            replacement_entry = (citation_match, corrected_citation, year, is_neutral)
          else:
            if 'Year' in citation_type:
              components = re.findall(r"\d+", citation_match)
              year = components[0]
            else: 
              year = 'No Year'
            replacement_entry = (citation_match, citation_match, year, is_neutral)
          REPLACEMENTS_CASELAW.append(replacement_entry)

        for abrv in doc._.abbreviations:
          # print(f"{abrv} \t ({abrv.start}, {abrv.end}) {abrv._.long_form}")
          abr_tuple = (abrv, abrv._.long_form)
          REPLACEMENTS_ABBR.append(abr_tuple)

        REPLACEMENTS_LEG = leg_pipeline(leg_titles, doc, nlp, db_conn)

        def removeDuplicates(lst):
          return [[a, b] for i, [a, b] in enumerate(lst) 
          if not any(c == b for _, c in lst[:i])]

        REPLACEMENTS_ABBR = removeDuplicates(REPLACEMENTS_ABBR)
        
      for replacement in REPLACEMENTS_CASELAW:
          file_data = replacer_caselaw(file_data, replacement)

      for replacement in list(set(REPLACEMENTS_LEG)):
        file_data = replacer_leg(file_data, replacement)
      
      for replacement in REPLACEMENTS_ABBR:
        file_data = replacer_abbr(file_data, replacement)
      
    output_file = f"output/{file}".replace(".xml", "_enriched.xml")

    with open(output_file, "w") as data_out:
        data_out.write(file_data)

close_connection(db_conn)