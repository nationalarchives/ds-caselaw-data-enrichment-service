import re

def apply_correction_strategy(citation_type, citation_match, canonical_form):
    """Find the appropriate correction strategy and apply it"""

    # e.g [2022] EWCA Civ 123
    if citation_type == "NCitYearAbbrNum":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        num = components[1]
        corrected_citation = canonical_form.replace("dddd", year).replace("d+", num)
    
    # e.g. [2022] EWHC 123 (Admin)
    # there's an argument for merging this with the NCitYearAbbrNum strategy
    elif citation_type == "NCitYearAbbrNumDiv":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        num = components[1]
        corrected_citation = canonical_form.replace("dddd", year).replace("d+", num)

    # e.g. [2022] UKFTT 2020_0341 (GRC)
    elif citation_type == "NCitYearAbbrNumUnderNumDiv":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        first_num = components[1]
        second_num = components[2]
        corrected_citation = canonical_form.replace("dddd", year).replace("d1", first_num).replace("d2", second_num)

    # e.g. [2022] UKET 123456/2022
    elif citation_type == "NCitYearAbrrNumStrokeNum":
        # TODO: rewrite this regex
        components = re.findall(r'\d+', citation_match)
        year = components[0]
        first_num = components[1]
        second_num = components[2]
        corrected_citation = canonical_form.replace("dddd", year).replace("d1", first_num).replace("d2", second_num)

    return corrected_citation
