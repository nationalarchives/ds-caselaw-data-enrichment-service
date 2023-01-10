"""
@author: editha.nemsic
This code corrects malformed citation matches.

- The choice of correction strategy is based on the type of citation match.
- Based on citation type the function retrieves the year and 1 or more digits from the citation match.
- The extracted information is used to build the well-formed citation using a canonical template that is being filled with the extracted year and digits.

"""

import re


def apply_correction_strategy(citation_type, citation_match, canonical_form):
    """
    Finds the appropriate correction strategy and applies it to the detected citation match.
    Parameters
    ----------
    citation_type : string
        type of citation that the detected citation match corresponds to (retrieved from Rules Manifest).
    citation_match : string
        detected citation match.
    canonical_form : string
        canoncial form template for the citation type corresponding to the detected citation match.
    Returns
    -------
    corrected_citation : string
        well-formed version of detected citation match.
    year : int or string
        year of cited case law
    d1/d2 : int/int or empty string
        digits building neutral citation for cited case law
    """

    # e.g [2022] EWCA Civ 123
    if (
        (citation_type == "NCitYearAbbrNum")
        | (citation_type == "NCitYearAbbrNumDiv")
        | (citation_type == "PubYearAbbrNum")
    ):
        # TODO: rewrite this regex
        components = re.findall(r"\d+", citation_match)
        year = components[0]
        d1 = components[1]
        d2 = ""
        corrected_citation = canonical_form.replace("dddd", year).replace("d+", d1)

    # e.g. [2022] UKFTT 2020_0341 (GRC)
    elif (
        (citation_type == "NCitYearAbbrNumUnderNumDiv")
        | (citation_type == "NCitYearAbrrNumStrokeNum")
        | (citation_type == "PubYearNumAbbrNum")
    ):
        # TODO: rewrite this regex
        components = re.findall(r"\d+", citation_match)
        year = components[0]
        d1 = components[1]
        d2 = components[2]
        corrected_citation = (
            canonical_form.replace("dddd", year).replace("d1", d1).replace("d2", d2)
        )

    elif (
        (citation_type == "PubAbbrNumAbbrNum")
        | (citation_type == "PubNumAbbrNum")
        | (citation_type == "EUCCase")
        | (citation_type == "EUTCase")
    ):
        components = re.findall(r"\d+", citation_match)
        year = "No Year"
        d1 = components[0]
        d2 = components[1]
        corrected_citation = canonical_form.replace("d1", d1).replace("d2", d2)

    return corrected_citation, year, d1, d2
