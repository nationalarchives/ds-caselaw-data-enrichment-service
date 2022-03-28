# -*- coding: utf-8 -*-
"""
Created on Mon Mar 3 10:48:33 2022

@author: Imane.Hafnaoui


Detects legislation references by searching through a lookup table of existing acts.
    - Exact matcher: searches the judgement for exact matches to the legislation title in lookup table.
    - Fuzzy matcher: detects well-formed and malformed citations (parameter: cutoff - confidence ratio to filter the search (min -> 90))
    - Hybrid matcher: narrows down the fuzzy matching to candidate segments in the judgement that contain the pattern [Act YYYY] and 
    performs exact matching otherwise.
    
"""
import pandas as pd
import bs4 as BeautifulSoup
from spacy.matcher import PhraseMatcher, Matcher
from spaczz.matcher import FuzzyMatcher
import sys
from time import time
from spacy.lang.en import English

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
def mergedict(x,b):
    a = {}
    for k,v in b.items(): a[k] = a.get(k, []) + b[k]
    for k,v in x.items(): a[k] = a.get(k, []) + x[k]
    return a

def detect_year_span(docobj, nlp):
    pattern = [{"SHAPE": "dddd"}]
    dmatcher = Matcher(nlp.vocab)
    dmatcher.add('date matcher', [pattern])
    dm = dmatcher(docobj)
    dates = [docobj[start:end].text for match_id, start, end in dm]
    dates = set([int(d) for d in dates if (len(d) == 4) & (d.isdigit())])
    return dates





def chunker(iterable, total_length, chunksize):
    return (iterable[pos: pos + chunksize] for pos in range(0, total_length, chunksize))


def flatten(list_of_lists):
    return [item for sublist in filter(None, list_of_lists) for item in sublist.items()]


def lookup_pipe(titles, docobj, nlp, method, cutoff=95):
    results = {}
    candidates = detectCandidate(
        nlp, docobj) if method.__name__ == 'hybrid' else None
    for title in nlp.pipe(titles, batch_size=100):
        matches = method(title.text, docobj, nlp, cutoff, candidates)
        if matches:
            results[title.text] = results.get(title.text, []) + matches
    return results

######


methods = {
    'exact': search_for_act,
    'fuzzy': search_for_act_fuzzy,
    'hybrid': hybrid
}

def main(argv):
    xml_path = argv[0]
    leg_path = argv[1]
    method = argv[2]

    print("Loading judgement...")
    with open(xml_path, "r", encoding="utf-8") as file_in:
        file_data = file_in.read()
    soup = BeautifulSoup.BeautifulSoup(str(file_data), "lxml")
    leg_content = soup.find_all("content")
    leg_content_text = " ".join([content.text for content in leg_content])

    print("Loading NLP corpus...")
    nlp = English()
    nlp.max_length = len(leg_content_text) #1500000
    docobj = nlp(leg_content_text)

    print("Loading legislation table...")
    # read leg-title lookup table
    leg_titles = pd.read_csv(leg_path)
    # limit search to years that appear in doc -- to be discussed with the team
    results = []
    dates = detect_year_span(docobj, nlp)
    shorttitles = leg_titles[leg_titles.year.isin(dates)]

    # run pipeline
    t = time()
    for fuzzy, method in zip([True, False], ('hybrid','exact')):
        titles = shorttitles[shorttitles.for_fuzzy==fuzzy].candidate_titles.drop_duplicates().tolist()
        res = lookup_pipe(titles, docobj, nlp, methods[method])
        results.append(res)
 
    results = mergedict(results[0], results[1])
    results = dict([(k, [dict(zip(keys, j)) for j in v])
                   for k, v in results.items()])    
    refs = [i for j in results.values() for i in j]
    t1 = time()
    #print(json.dumps(results, indent=(4)))
    print('%s--> Detected %d legislations in %d (s): %d references' %
           (xml_path, len(results), (t1-t), len(refs)))
    # return t1-t, len(results), len(refs), xml_path


if __name__ == "__main__":
    main(sys.argv[1:])