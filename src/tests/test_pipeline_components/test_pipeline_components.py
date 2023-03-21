import pytest

pytest.skip(allow_module_level=True)
# it's really not clear what these tests are supposed to be, maybe we should just delete them

"""
Individual testing componenets that can be integrated into the pipeline,
and which do not require any other testing data.
"""

"""
Param: case law replacements
Verifies the replacements have the required data
"""


def test_replacement_caselaw(caselaw):
    assert isinstance(caselaw, list)
    for replacement in list(set(caselaw)):
        assert replacement[0] is not None
        assert replacement[1] is not None
        assert replacement[2] is not None
        assert replacement[3] is not None
        assert (
            str(replacement[4]).lower() == "true"
            or str(replacement[4]).lower() == "false"
        )


"""
Param: legislation replacements
Verifies the replacements have the required data
"""


def test_replacement_legislation(legislation):
    assert isinstance(legislation, list)
    for replacement in list(set(legislation)):
        assert replacement[0] is not None
        assert replacement[1] is not None


"""
Param: abbreviation replacements
Verifies the replacements have the required data
"""


def test_replacement_abbreviations(abbreviations):
    assert isinstance(abbreviations, list)
    for replacement in list(set(abbreviations)):
        assert replacement[0] is not None
        assert replacement[1] is not None


"""
Param: replaced caselaw
Verifies they have been successfully replaced
"""


def test_replacer_caselaw(caselaw):
    case_tag = '<ref type="case"'
    year_tag = "year="
    canonical_tag = "canonical_form="
    closing_tag = "</ref>"
    assert case_tag in caselaw
    assert year_tag in caselaw
    assert canonical_tag in caselaw
    assert closing_tag in caselaw


"""
Param: replaced legislation
Verifies they have been successfully replaced
"""


def test_replacer_legsilation(legislation):
    leg_tag = '<ref type="legislation" href='
    assert leg_tag in legislation


"""
Param: replaced abbreviations
Verifies they have been successfully replaced
"""


def test_replacer_abbreviations(abbreviations):
    abbrv_open_tag = "<abbr title="
    abbrv_close_tag = "</abbr>"
    assert abbrv_open_tag in abbreviations
    assert abbrv_close_tag in abbreviations
