"""
Created on Mon Mar 3 10:48:33 2022

@author: Imane.Hafnaoui


Detects legislation references by searching through a lookup table of existing acts. We do this through a hybrid approach that merges exact and fuzzy matching.
The hybrid matcher goes through three stages:
    Stage 1:
        - Narrows down the search space to candidate segments in the judgement text that contain the pattern [Act YYYY]; and
        - Performs the fuzzy matching against legislation in the lookup table.Then;
    Stage 2:
        - Runs exact matching against the entries in the table that don't fit the [Act YYYY] pattern (e.g. RCRA 1926).
    Stage 3:
        - Merges the results of Stages 1 & 2;
        - Resolves detected references that might overlap due the nature of the fuzzy matching to a [1-to-1] linking between legislation title and detected reference.
        - Creates replacement tuples for the detected references

"""
from collections import namedtuple
from typing import Any, List

import numpy as np
import pandas as pd
from spacy.matcher import Matcher, PhraseMatcher
from spaczz.matcher import FuzzyMatcher

from database.db_connection import get_canonical_leg, get_hrefs

CUTOFF = 90
PAD = 5

keys = ["detected_ref", "start", "end", "confidence", "ref", "canonical"]
leg = namedtuple("leg", "detected_ref href canonical")


def mergedict(x, b):
    """
    Merges two dictionaries together
    Parameters
    ----------
    x : dict
        Dictionary containing the detected references from fuzzy matching.
    b : dict
        Dictionary containing the detected references from exact matching.
    Returns
    -------
    outout : dict
        dictionary containing the detected references.
    """
    a: dict[Any, Any] = {}
    for k, v in b.items():
        a[k] = a.get(k, []) + b[k]
    for k, v in x.items():
        a[k] = a.get(k, []) + x[k]
    return a


def resolve_overlap(results_dict):
    """
    Resolves references that have been detected as legislation but overlap in the body of judgement to the most accurate legislation.
    This might occur due to the nature of the fuzzy matching where it matches two closely worded legislation to the same text in a judgement.
    This function ensures a 1-to-1 linkage between a legislation title and a detected reference.
    Parameters
    ----------
    results_dict : dict
        Dictionary containing the detected references.
    Returns
    -------
    outout : dict
        dictionary containing the detected references with overlapped references removed.
    """
    qq = pd.DataFrame([results_dict])
    qq = qq.T.explode(0)[0].apply(pd.Series)

    qq.columns = keys

    # get refs that overlap in the text
    mask = (qq.start.values[:, None] >= qq.start.values) & (
        qq.end.values[:, None] <= qq.end.values
    )
    np.fill_diagonal(mask, 0)  # omit 'pairs' that are the same thing twice
    mask = np.triu(mask, 0)  # omit pairs where the first is after than the second
    r, c = np.where(mask)
    overlaps = list(map(list, zip(r, c)))

    removals = set()

    qq = qq.reset_index()

    # for every detected pair of refs that overlap
    for ol_index in overlaps:
        # get those two rows
        overlap_rows = qq.iloc[list(ol_index)]
        # get the worst of the two (or first, if they're equal)
        worst_match_index = overlap_rows.confidence.idxmin()
        # and mark its index for deletion
        removals.add(worst_match_index)

    # then drop all the removed entries at once
    for removal in removals:
        qq.drop(index=removal, inplace=True)

    retval = (
        qq.set_index("index")
        .apply(tuple, axis=1)
        .groupby("index")
        .apply(list)
        .T.to_dict()
    )
    return retval


# EXACT MATCHING


def exact_matcher(title, docobj, nlp, cutoff=None, candidates=None):
    """
    Detects legislation in body of judgement by searching for the exact match of the title in the text.
    Parameters
    ----------
    title : string
        Title of a legislation.
    docobj : spacy.Doc
        The body of the judgement.
    nlp : spacy.English
        English NLP module.
    Returns
    -------
    matched_text : list(tuple)
        List of tuples of the form ('detected reference', 'start position', 'end position', 100)
    """
    phrase_matcher = PhraseMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    phrase_matcher.add("Text Extractor", None, *phrase_list)

    matched_items = phrase_matcher(docobj)

    matched_text = []
    for _, start, end in matched_items:
        span = docobj[start:end]
        matched_text.append((span.text, start, end, 100))
    return matched_text


# FUZZY MATCHING


def search_for_act_fuzzy(title, docobj, nlp, cutoff, candidates=None):
    """
    Detects well-formed and malformed references to a legislation title in the judgement body.
    Parameters
    ----------
    title : string
        Title of a legislation.
    docobj : spacy.Doc
        The body of the judgement.
    nlp : spacy.English
        English NLP module.
    cutoff : int
        Value to determine the level of similarity of matches to be returned by the fuzzy matcher.
        Eg. a match between two string with a ratio of 90 and cutoff 95 would not be returned by the matcher.
    candidates : list(tuple)
        List of tuples in the form [(start_pos, end_pos)] indicating the position of the candidate segments in the text.
    Returns
    -------
    matched_text : list(tuple)
        List of tuples of the form ('detected reference', 'start position', 'end position', 'similarity')
    """

    fuzzy_matcher = FuzzyMatcher(nlp.vocab)
    phrase_list = [nlp(title)]
    options = {"fuzzy_func": "token_sort", "min_r1": 70, "min_r2": cutoff}
    fuzzy_matcher.add("Text Extractor", phrase_list, kwargs=[options])
    matched_items = fuzzy_matcher(docobj)
    matched_text = []
    for _, start, end, ratio, pattern in matched_items:
        span = docobj[start:end]
        matched_text.append((span.text, start, end, ratio))
    return matched_text


def fuzzy_matcher(title, docobj, nlp, cutoff, candidates=None):
    """
    Detects legislation in body of judgement by searching the candidate segments for similar matches of the title by running a fuzzy matcher.
    Parameters
    ----------
    title : string
        Title of a legislation.
    docobj : spacy.Doc
        The body of the judgement.
    nlp : spacy.English
        English NLP module.
    cutoff : int
        Value to determine the level of similarity of matches to be returned by the fuzzy matcher.
        Eg. a match between two string with a ratio of 90 and cutoff 95 would not be returned by the matcher.
    candidates : list(tuple)
        List of tuples in the form [(start_pos, end_pos)] indicating the position of the candidate segments in the text.
    Returns
    -------
    matched_text : list(tuple)
        List of tuples of the form ('detected reference', 'start position', 'end position', 'similarity')
    """
    # split the year refernce from the act title
    act, year = title[:-4], title[-4:]
    # get the span of the act title to be searched
    act_span = len(nlp(title)) + PAD
    all_matches = []
    for _, end in candidates:
        # get segment in judgment that contains candidate reference
        segment = nlp(docobj[end - act_span : end - 1].text)
        dyear = docobj[end - 1 : end].text
        # fuzzy match act with segment
        matches = search_for_act_fuzzy(act, segment, nlp, cutoff=cutoff)
        if (len(matches) > 0) & (dyear == year):
            all_matches.extend(
                [
                    (docobj[end - 1 - e + s : end].text, end - 1 - e + s, end, ratio)
                    for text, s, e, ratio in matches
                ],
            )
    return all_matches


def detect_candidates(nlp, docobj):
    """
    Detect possible legislation references with pattern [Act YYYY].
    Parameters
    ----------
    docobj : spacy.Doc
        The body of the judgement.
    nlp : spacy.English
        English NLP module.
    Returns
    -------
    output : list(tuple)
        List of tuples indicating the position of the candidate segments in the text.
    """
    #
    pattern = [{"ORTH": "Act"}, {"SHAPE": "dddd"}]
    matcher = Matcher(nlp.vocab)
    matcher.add("Act Matcher", [pattern])
    matches = matcher(docobj)
    return [(start, end) for _, start, end in matches]


def lookup_pipe(titles, docobj, nlp, method, conn, cutoff):
    """
    Executes the 'method' matcher againt the judgement body to detect legislations.
    Parameters
    ----------
    titles : list(string)
        List of legislation titles.
    docobj : spacy.Doc
        The body of the judgement.
    nlp : spacy.English
        English NLP module.
    method : function
        Function specifying which matcher to execute (fuzzy or exact).
    conn : database connection
        Database connection to the legislation look-up table.
    cutoff : int
        Value to determine the level of similarity of matches to be returned by the fuzzy matcher.
        Eg. a match between two string with a ratio of 90 and cutoff 95 would not be returned by the matcher.
    Returns
    -------
    results : list(dict)
        List of dictionaries of the form {
            'detected_ref'(string): 'detected reference in the judgement body',
            'ref'(string): 'matched legislation title',
            'canonical'(string): 'canonical form of legislation act',
            'start'(int): 'start position of reference',
            'end'(int): 'end positin of reference',
            'confidence'(int): 'matching similarity between detected_ref and ref'}
    """
    results: dict[str, List[Any]] = {}
    # get candidate segments matching the pattern [Act YYYY]
    candidates = (
        detect_candidates(nlp, docobj) if method.__name__ == "fuzzy_matcher" else None
    )
    # for every legislation title in the table
    for title in nlp.pipe(titles, batch_size=100):
        # detect legislation in the judgement body
        matches = method(title.text, docobj, nlp, cutoff, candidates)
        if matches:
            # pull relevant information from database and append to detected reference
            href = get_hrefs(conn, title.text)
            canonical = get_canonical_leg(conn, title.text)
            matches_with_refs = []
            for match in matches:
                match_list = list(match)
                match_list.append(href)
                match_list.append(canonical)
                match = tuple(match_list)
                matches_with_refs.append(match)
            results[title.text] = results.get(title.text, []) + matches_with_refs
    return results


def detect_year_span(docobj, nlp):
    """
    Detects year -like text in the judgement body.
    Parameters
    ----------
    docobj : spacy.Doc
        The body of the judgement.
    nlp : spacy.English
        English NLP module.
    Returns
    -------
    dates : list[string]
        List of year -like strings.
    """
    pattern = [{"SHAPE": "dddd"}]
    dmatcher = Matcher(nlp.vocab)
    dmatcher.add("date matcher", [pattern])
    dm = dmatcher(docobj)
    string_dates = [docobj[start:end].text for _, start, end in dm]
    dates = set([int(d) for d in string_dates if (len(d) == 4) & (d.isdigit())])
    return dates


######


methods = {"exact": exact_matcher, "fuzzy": fuzzy_matcher}


def leg_pipeline(leg_titles, nlp, docobj, conn):
    """
    Merges dictionary results of fuzzy and exact matching functions
    Parameters
    ----------
    leg_titles: list(string)
        List of legislation titles.
    nlp : spacy.English
    English NLP module.
    docobj : spacy.Doc
        The body of the judgement.
    conn : database connection
        Database connection to the legislation look-up table.
    Returns
    -------
    List[Tuple[Str, Str, Str]], of merged results of both matchers to list of tupled references
        'detected_ref'(string): 'detected reference in the judgement body',
        'ref'(string): 'matched legislation title',
        'canonical'(string): 'canonical form of legislation act'
    """
    result_list = []
    dates = detect_year_span(docobj, nlp)
    # filter the legislation list down to the years detected above
    titles = leg_titles[leg_titles.year.isin(dates)]

    for fuzzy, method in zip([True, False], ("fuzzy", "exact")):
        # select the titles relevant to the approach to be run using the 'for_fuzzy' flag already built into the look-up table
        relevant_titles = (
            titles[titles.for_fuzzy == fuzzy]
            .candidate_titles.drop_duplicates()
            .tolist()
        )
        res = lookup_pipe(relevant_titles, docobj, nlp, methods[method], conn, CUTOFF)
        result_list.append(res)

    # merges the results of both matchers to return a single list of detected references
    results = mergedict(result_list[0], result_list[1])

    results = resolve_overlap(results) if results else results

    results = dict([(k, [dict(zip(keys, j)) for j in v]) for k, v in results.items()])
    refs = [i for j in results.values() for i in j]

    # keys_to_extract = {'detected_ref', 'ref'}
    replacements = []
    for ref in refs:
        detected_ref = ref["detected_ref"]
        href = ref["ref"]
        canonical_form = ref["canonical"]
        replacement = leg(detected_ref, href, canonical_form)
        replacements.append(replacement)
    print(f"Found {len(replacements)} legislation replacements")

    return replacements
