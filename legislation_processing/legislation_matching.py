# -*- coding: utf-8 -*-
"""
Created on Mon Mar 3 10:48:33 2022

@author: Imane.Hafnaoui
"""
import pandas as pd
import spacy, sys
import bs4 as BeautifulSoup
from spacy.matcher import PhraseMatcher, Matcher
from spaczz.matcher import FuzzyMatcher
from joblib import Parallel, delayed
import  json
from time import time
from spacy.lang.en import English

cpus = 100
chunksize = 50
keys=['detected_ref','start','end','confidence']

#### EXACT MATCHING

def search_for_act(title, doc_obj, nlp):
    #print(title)
    phrase_matcher = PhraseMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    phrase_matcher.add("Text Extractor", None, *phrase_list)

    matched_items = phrase_matcher(doc_obj)

    matched_text = []
    for match_id, start, end in matched_items:
        span = doc_obj[start: end]
        matched_text.append((span.text, start, end))
    return matched_text

#### FUZZY MATCHING

def search_for_act_fuzzy(title, doc_obj, nlp, cutoff=95):
    #TODO: use a hybrid methofor year disambiguation
    fuzzy_matcher = FuzzyMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    options={"fuzzy_func": "token_sort", "min_r1":90, "min_r2":cutoff}
    fuzzy_matcher.add("Text Extractor",  phrase_list, kwargs=[options])
    matched_items = fuzzy_matcher(doc_obj)
    matched_text = []
    for match_id, start, end, ratio in matched_items:
        span = doc_obj[start: end]
        matched_text.append((span.text, start, end, ratio))
    return matched_text

def detect_year_span(docobj, nlp): #TODO: find better way
    pattern = [{"SHAPE": "dddd"}]
    dmatcher = Matcher(nlp.vocab)
    dmatcher.add('date matcher', [pattern])
    dm = dmatcher(docobj)  
    dates = [docobj[start:end].text for match_id, start, end in dm]    
    dates=set([int(d) for d in dates if (len(d)==4) & (d.isdigit())])
    return dates


methods = {
    'exact': search_for_act,
    'fuzzy': search_for_act_fuzzy
    }
#### MULTIPROC

def chunker(iterable, total_length, chunksize):
    return (iterable[pos: pos + chunksize] for pos in range(0, total_length, chunksize))

def flatten(list_of_lists):
    return [item for sublist in filter(None,list_of_lists) for item in sublist.items()]
       
def lookup_pipe(titles, doc_obj, nlp, method):
    results = {}
    for title in nlp.pipe(titles, batch_size=10):
        matches = method(title, doc_obj, nlp)
        if matches: 
            results[title.text] = results.get(title.text, []) + matches
    return results

def lookup_parallel(titles, docobj, nlp, method, chunksize=150, cpus=1):
    executor = Parallel(n_jobs=cpus, backend='multiprocessing', prefer="processes")
    do = delayed(lookup_pipe)
    tasks = (do(chunk, docobj, nlp, method) for chunk in chunker(titles, len(titles), chunksize=chunksize))
    result = executor(tasks)
    return flatten(result)

######

def main(argv):
    xml_path = argv[0]
    leg_path = argv[1]
    method = argv[2]
    
    print("Loading judgement...")
    with open(xml_path, "r", encoding="utf-8") as file_in:
           file_data = file_in.read()
    soup = BeautifulSoup.BeautifulSoup(str(file_data), "lxml")
    leg_content = soup.find_all("content")
    leg_content_text = " ".join(    [content.text for content in leg_content])
    
    print("Loading NLP corpus...")
    # spacy english model (small)
    #nlp = spacy.load('en_core_web_sm')
    nlp = English()
    nlp.max_length = 1500000
    docobj = nlp(leg_content_text)
    
    print("Loading legislation table...")
    # read leg-title lookup table
    leg_titles = pd.read_csv(leg_path)
    # limit search to years that appear in doc -- to be discussed with the team
    dates = detect_year_span(docobj, nlp)
    shorttitles = leg_titles[leg_titles.year.isin(dates)].shorttitle.dropna().drop_duplicates().tolist()
    
    print("Matching in progress...", len(shorttitles))
    # run pipeline
    t = time()
    res = lookup_parallel(shorttitles, docobj, nlp, methods[method], chunksize, cpus)
    t1 = time()
    results = dict([(k,[dict(zip(keys, j)) for j in v]) for k,v in res])
    refs = [i for j in results.values() for i in j]
    print(json.dumps(results, indent=(4)))
    print('--> Detected %d legislations in %d (s): %d references out of  ""'%(len(results),(t1-t), len(refs)))

if __name__ == "__main__":
   main(sys.argv[1:])
