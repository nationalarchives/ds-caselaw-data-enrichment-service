# -*- coding: utf-8 -*-
"""
Created on Mon Mar 3 10:48:33 2022

@author: Imane.Hafnaoui
"""
import pandas as pd
import spacy
import bs4 as BeautifulSoup
from spaczz.matcher import FuzzyMatcher, Matcher
from joblib import Parallel, delayed

file_path = 'tmp'
leg_path = 'tmp'

with open(file_path, "r", encoding="utf-8") as file_in:
       file_data = file_in.read()
soup = BeautifulSoup.BeautifulSoup(str(file_data), "lxml")
leg_content = soup.find_all("content")
leg_content_text = " ".join(    [content.text for content in leg_content])
            
# spacy english model (small)
nlp = spacy.load('en_core_web_sm')
docobj = nlp(leg_content_text)

# read leg-title lookup table
leg_titles = pd.read_csv(leg_path)

#### FUZZY MATCHING

def search_for_act_fuzzy(title, doc_obj, nlp, cutoff=95):
    fuzzy_matcher = FuzzyMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    options={"fuzzy_func": "token_sort", "min_r1":90, "min_r2":cutoff}
    fuzzy_matcher.add("Text Extractor",  phrase_list, kwargs=[options])
    matched_items = fuzzy_matcher(doc_obj)
    matched_text = []
    for match_id, start, end, ratio in matched_items:
        span = doc_obj[start: end]
        matched_text.append((span.text, ratio))
    return matched_text

def detect_year_span(docobj): #TODO: find better way
    pattern = [{"SHAPE": "dddd"}]
    dmatcher = Matcher(nlp.vocab)
    dmatcher.add('date matcher', [pattern])
    dm = dmatcher(docobj)  
    dates = [docobj[start:end].text for match_id, start, end in dm]    
    dates=set([int(d) for d in dates if (len(d)==4) & (d.isdigit())])
    return dates


#### MULTIPROC

def chunker(iterable, total_length, chunksize):
    return (iterable[pos: pos + chunksize] for pos in range(0, total_length, chunksize))

def flatten(list_of_lists):
    return [item for sublist in filter(None,list_of_lists) for item in sublist.items()]
       
def lookup_pipe(titles, doc_obj, nlp):
    results = {}
    for title in nlp.pipe(titles, batch_size=100):
        matches = search_for_act_fuzzy(title, doc_obj, nlp)
        if matches: 
            results[title.text] = results.get(title.text, []) + matches
    return results

def lookup_parallel(titles, docpbj, nlp, chunksize=150):
    executor = Parallel(n_jobs=16, backend='multiprocessing', prefer="processes")
    do = delayed(lookup_pipe)
    tasks = (do(chunk, docobj, nlp) for chunk in chunker(titles, len(titles), chunksize=chunksize))
    result = executor(tasks)
    return flatten(result)

######
# limit search to years that appear in doc -- to be discussed with the team
dates = detect_year_span(docobj)
shorttitles = leg_titles[leg_titles.year.isin(dates)].shorttitle.dropna()

# run pipeline
res = lookup_parallel(shorttitles, docobj, nlp)
