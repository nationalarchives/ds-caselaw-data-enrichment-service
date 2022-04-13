# -*- coding: utf-8 -*-
"""
Created on Mon Mar 3 10:48:33 2022

@author: Imane.Hafnaoui


Detects legislation references by searching through a lookup table of existing acts.
    - Exact matcher: searches the judgement for exact matches to the legislation title in lookup table.
    - Fuzzy matcher: detects well-formed and malformed citations (parameter: cutoff - confidence ratio to filter the search (min -> 90))
    - Hybrid matcher: narrows down the fuzzy matching to candidate segments in the judgement that contain the pattern [Act YYYY]
    
"""
import pandas as pd
import bs4 as BeautifulSoup
from spacy.matcher import PhraseMatcher, Matcher
from spaczz.matcher import FuzzyMatcher
from joblib import Parallel, delayed
import json
import sys
from time import time
from spacy.lang.en import English

cpus = 100
chunksize = 50
keys = ['detected_ref', 'start', 'end', 'confidence']

# EXACT MATCHING


def search_for_act(title, doc_obj, nlp, cutoff=None, candidates=None):
    # print(title)
    phrase_matcher = PhraseMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    phrase_matcher.add("Text Extractor", None, *phrase_list)

    matched_items = phrase_matcher(doc_obj)

    matched_text = []
    for match_id, start, end in matched_items:
        span = doc_obj[start: end]
        matched_text.append((span.text, start, end))
    return matched_text

# FUZZY MATCHING


def search_for_act_fuzzy(title, doc_obj, nlp, cutoff=95, candidates=None):
    fuzzy_matcher = FuzzyMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    options = {"fuzzy_func": "token_sort", "min_r1": 90, "min_r2": cutoff}
    fuzzy_matcher.add("Text Extractor",  phrase_list, kwargs=[options])
    matched_items = fuzzy_matcher(doc_obj)
    matched_text = []
    for match_id, start, end, ratio in matched_items:
        span = doc_obj[start: end]
        matched_text.append((span.text, start, end, ratio))
    return matched_text

# HYBRID MATCHING


def detectCandidate(nlp, docobj):
    # detect possible legislation refs with pattern [Act YYYY]
    pattern = [{"ORTH": "Act"}, {"SHAPE": "dddd"}]
    matcher = Matcher(nlp.vocab)
    matcher.add('Act Matcher', [pattern])
    matches = matcher(docobj)
    return [(start, end) for match_id, start, end in matches]


def hybrid(title, docobj, nlp, cutoff=95, candidates=None):
    act, year = title[:-4], title[-4:]
    act_span = len(nlp(title))
    all_matches = []
    for _, end in candidates:
        # get segment in judgment that contains candidate ref
        segment = nlp(docobj[end-act_span:end-1].text)
        dyear = docobj[end-1:end].text
        # fuzzy match act with segment
        matches = search_for_act_fuzzy(act, segment, nlp, cutoff=cutoff)
        if (len(matches) > 0) & (dyear == year):
            all_matches.extend(
                [(docobj[end-1-e+s:end].text, end-1-e+s, end, ratio) for text, s, e, ratio in matches])
    return all_matches

######

def detect_year_span(docobj, nlp):  # TODO: to be discussed - enforces reference to have a year
    pattern = [{"SHAPE": "dddd"}]
    dmatcher = Matcher(nlp.vocab)
    dmatcher.add('date matcher', [pattern])
    dm = dmatcher(docobj)
    dates = [docobj[start:end].text for match_id, start, end in dm]
    dates = set([int(d) for d in dates if (len(d) == 4) & (d.isdigit())])
    return dates


methods = {
    'exact': search_for_act,
    'fuzzy': search_for_act_fuzzy,
    'hybrid': hybrid
}

# MULTIPROC


def chunker(iterable, total_length, chunksize):
    return (iterable[pos: pos + chunksize] for pos in range(0, total_length, chunksize))


def flatten(list_of_lists):
    return [item for sublist in filter(None, list_of_lists) for item in sublist.items()]


def lookup_pipe(titles, docobj, nlp, method, cutoff=95):
    results = {}
    candidates = detectCandidate(
        nlp, docobj) if method.__name__ == 'hybrid' else None
    for title in nlp.pipe(titles, batch_size=10):
        matches = method(title.text, docobj, nlp, cutoff, candidates)
        if matches:
            results[title.text] = results.get(title.text, []) + matches
    return results


def lookup_parallel(titles, docobj, nlp, method, chunksize=150, cpus=1):
    executor = Parallel(
        n_jobs=cpus, backend='multiprocessing', prefer="processes")
    do = delayed(lookup_pipe)
    tasks = (do(chunk, docobj, nlp, method)
             for chunk in chunker(titles, len(titles), chunksize=chunksize))
    result = executor(tasks)
    return flatten(result)

######


def main(argv):
    xml_path = argv[0]
    leg_path = argv[1]
    method = argv[2]

    # print("Loading judgement...")
    with open(xml_path, "r", encoding="utf-8") as file_in:
        file_data = file_in.read()
    soup = BeautifulSoup.BeautifulSoup(str(file_data), "lxml")
    leg_content = soup.find_all("content")
    leg_content_text = " ".join([content.text for content in leg_content])

    # print("Loading NLP corpus...")
    # spacy english model (small)
    #nlp = spacy.load('en_core_web_sm')
    nlp = English()
    nlp.max_length = len(leg_content_text)
    docobj = nlp(leg_content_text)

    # print("Loading legislation table...")
    # read leg-title lookup table
    leg_titles = pd.read_csv(leg_path)
    # limit search to years that appear in doc -- to be discussed with the team
    # print('detecting dates...')
    dates = detect_year_span(docobj, nlp)
    shorttitles = leg_titles[leg_titles.year.isin(dates)].candidate_titles.drop_duplicates().tolist()
    
    # shorttitles = leg_titles.candidate_titles

    # print("Matching in progress...", len(shorttitles))
    # run pipeline
    t = time()
    res = lookup_pipe(shorttitles, docobj, nlp, methods[method])
    t1 = time()
    results = dict([(k, [dict(zip(keys, j)) for j in v])
                   for k, v in res.items()])
    refs = [i for j in results.values() for i in j]
    # print(json.dumps(results, indent=(4)))
    # print('--> Detected %d legislations in %d (s): %d references out of  ""' %
          # (len(results), (t1-t), len(refs)))
    return t1-t, len(results), len(refs), xml_path

if __name__ == "__main__":
    main(sys.argv[1:])