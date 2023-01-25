# -*- coding: utf-8 -*-
"""
Replacer logic for second and third phase enrichment. 
Handles the replacements of oblique references and legislation provisions. 
"""


import re
from itertools import groupby

from bs4 import BeautifulSoup


def splitString(text, split_points):
    """
    Splits a string at locations in the text where a reference was detected 
    :param text: XML file
    :param split_points: list of positions of matches
    :return: list of split strings
    """
    return list(
        map(lambda x: text[slice(*x)], zip(split_points, split_points[1:] + [None]))
    )


def replacer(text, detected_refs):
    """
    String replacement with matches from references 
    :param text: XML file
    :param detected_refs: list of dict of detected references
    :return: enriched XML file data
    """
    split_points = [match["ref_position"] for match in detected_refs]
    split_text = splitString(text, split_points)
    enriched_text = text[: split_points[0]]
    for spt, match in zip(split_text, detected_refs):
        enriched_text += re.sub(re.escape(match["detected_ref"]), match["ref_tag"], spt)

    return enriched_text


def provision_replacement(file_data, replacements):
    """
    String replacement in the XML
    :param file_data: XML file
    :param replacements: list of dict of resolved provisions
    :return: enriched XML file data
    """

    def key_func(k):
        return k["ref_para"]

    paras = file_data.find_all("p")
    relevant_paras = sorted(replacements, key=key_func)

    for p, matches in groupby(relevant_paras, key=key_func):
        new_txt = BeautifulSoup(replacer(str(paras[p]), list(matches)), "lxml")
        paras[p].replace_with(new_txt.p)
    return str(file_data)


def oblique_replacement(file_data, replacements):
    """
    String replacement in the XML
    :param file_data: XML file
    :param replacements: list of dict of resolved oblique refs
    :return: enriched XML file data
    """
    enriched_text = replacer(file_data, replacements)
    return enriched_text
