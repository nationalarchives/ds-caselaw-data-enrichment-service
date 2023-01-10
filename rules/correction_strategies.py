"""
@author: editha.nemsic
Correct strategies for the case law replacements. 
:param citation_type: Citation pattern 
:param citation_match: Citation that was matched 
:param canonical_form: Canonical form of the citation
"""


import re


def apply_correction_strategy(citation_type, citation_match, canonical_form):
    """Find the appropriate correction strategy and apply it"""

    # e.g [2022] EWCA Civ 123
    if (
        (citation_type == "NCitYearAbbrNum")
        | (citation_type == "NCitYearAbbrNumDiv")
        | (citation_type == "PubYearAbbrNum")
    ):
        # TODO: rewrite this regex
        components = re.findall(r"\d+", citation_match)
        year = components[0]
        num = components[1]
        corrected_citation = canonical_form.replace("dddd", year).replace("d+", num)

    # e.g. [2022] UKFTT 2020_0341 (GRC)
    elif (
        (citation_type == "NCitYearAbbrNumUnderNumDiv")
        | (citation_type == "NCitYearAbrrNumStrokeNum")
        | (citation_type == "PubYearNumAbbrNum")
    ):
        # TODO: rewrite this regex
        components = re.findall(r"\d+", citation_match)
        year = components[0]
        first_num = components[1]
        second_num = components[2]
        corrected_citation = (
            canonical_form.replace("dddd", year)
            .replace("d1", first_num)
            .replace("d2", second_num)
        )

    elif (
        (citation_type == "PubAbbrNumAbbrNum")
        | (citation_type == "PubNumAbbrNum")
        | (citation_type == "EUCCase")
        | (citation_type == "EUTCase")
    ):
        components = re.findall(r"\d+", citation_match)
        year = "No Year"
        first_num = components[0]
        second_num = components[1]
        corrected_citation = canonical_form.replace("d1", first_num).replace(
            "d2", second_num
        )

    return corrected_citation, year
