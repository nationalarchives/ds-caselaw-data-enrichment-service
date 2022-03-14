import os
import re
import pandas as pd
from collections import Counter
from tqdm import tqdm
import json

from spacy.lang.en import English
import bs4 as BeautifulSoup

from helper import parse_file, load_patterns
from db_connection import create_connection, close_connection, get_matched_rule
from correction_strategies import apply_correction_strategy
from replacer import replacer
from analysis import pie_malformed, bar_citation_types, bar_citation_year, bar_malformed_type, citations_hist

ROOTDIR = "../tna-sample/tna-sample/tna-sample"
DATABASE = "manifest.db"
db_conn = create_connection(DATABASE)
load_patterns(db_conn)

nlp = English()
nlp.max_length = 2500000
citation_ruler = nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")

MATCHED_RULE_ID = []
WELL_FORMED = 0
MALFORMED = 0
MATCHED_RULE_TYPE = []
YEARS = []
TYPE_MALFORMED = []
CITATIONS_PER_DOC = []
benchmark_dict = {'filename': [], 'rule_id': [], 'citation': []}

for subdir, dirs, files in os.walk(ROOTDIR):
  for file in tqdm(files):
    if not file.startswith('.'):
      REPLACEMENTS = []
      file_path = os.path.join(subdir, file)
      if not file_path == '../tna-sample/tna-sample/tna-sample/ewhc/fam/2021/2021-ewhc-65-fam.xml':
        with open(file_path, "r", encoding="utf-8") as file_in:
          print(file)
          file_data = file_in.read()
          judgment_content_text = parse_file(file_data)
          doc = nlp(judgment_content_text)
          CITATIONS_PER_DOC.append(len(doc.ents))
          for ent in doc.ents:
            rule_id = ent.ent_id_
            citation_match = ent.text
            benchmark_dict['filename'].append(file)
            benchmark_dict['rule_id'].append(rule_id)
            benchmark_dict['citation'].append(citation_match)
            MATCHED_RULE_ID.append(rule_id)
            is_canonical, citation_type, canonical_form, description = get_matched_rule(db_conn, rule_id)
            MATCHED_RULE_TYPE.append(description)
            if is_canonical == False:
              MALFORMED += 1
              corrected_citation, year = apply_correction_strategy(citation_type, citation_match, canonical_form)
              print ("-----> CORRECTED:", corrected_citation, file)
              replacement_entry = (citation_match, corrected_citation, year)
              YEARS.append(year)
              TYPE_MALFORMED.append(description)
            else:
              WELL_FORMED += 1
              if 'Year' in citation_type:
                components = re.findall(r"\d+", citation_match)
                year = components[0]
              else: 
                year = 'No Year'
              replacement_entry = (citation_match, citation_match, year)
              YEARS.append(year)
            REPLACEMENTS.append(replacement_entry)
        
        for replacement in REPLACEMENTS:
            file_data = replacer(file_data, replacement)
        
        output_file = f"output/{file}".replace(".xml", "_enriched.xml")

        with open(output_file, "w") as data_out:
            data_out.write(file_data)

with open('benchmark.json', 'w') as f:
  json.dump(benchmark_dict, f)
close_connection(db_conn)
pie_malformed(WELL_FORMED, MALFORMED)
bar_citation_types(MATCHED_RULE_TYPE)
bar_citation_year(YEARS)
bar_malformed_type(TYPE_MALFORMED)
citations_hist(CITATIONS_PER_DOC)