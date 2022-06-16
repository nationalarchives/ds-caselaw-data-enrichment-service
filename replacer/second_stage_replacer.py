#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 11:21:36 2022

@author: imane.hafnaoui
"""

import re

def splitString(text, split_points):
    return list(map(lambda x: text[slice(*x)], zip(split_points, split_points[1:]+[None])))


def detected_references_replacement(text, detected_refs):
    split_points = [match['ref_position'] for match in detected_refs]
    split_text = splitString(text, split_points)
    new_text = []
    for spt, match in zip(split_text, detected_refs):
        new_text.append(re.sub(match['ref'], match['enriched_ref'], spt))
    
    return ''.join(new_text)