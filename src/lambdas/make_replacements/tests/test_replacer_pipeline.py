import unittest

from lambdas.make_replacements.replacer_pipeline import (
    replacer_abbr,
    replacer_caselaw,
    replacer_leg,
)


class TestCitationReplacer(unittest.TestCase):
    """
    This class tests the replacement of the citations within the text itself.
    """

    def test_citation_replacer(self):
        citation_match = "[2025] 1 All E.R. 123"  # incorrect citation
        corrected_citation = (
            "[2025] 1 All ER 123"  # in practice, returned via the citation matcher
        )
        year = "2025"
        URI = "#"
        is_neutral = "true"
        text = "In the judgment the incorrect citation is [2025] 1 All E.R. 123."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "[2022] UKET 789123_2012"
        corrected_citation = "[2022] UKET 789123/2012"
        year = "2022"
        URI = "#"
        is_neutral = "true"
        text = "This citation that needs to be changed is [2022] UKET 789123_2012 which discussed..."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "LR 1 A&E 123"
        corrected_citation = "LR 1 AE 123"
        year = "No Year"
        text = "LR 1 A&E 123 refers to..."
        URI = "#"
        is_neutral = "true"
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "(2022) EWHC 123 (Mercantile)"
        corrected_citation = "[2022] EWHC 123 (Mercantile)"
        year = "2022"
        URI = "#"
        is_neutral = "true"
        text = "I defer to the judgment in (2022) EWHC 123 (Mercantile)."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry

        citation_match = "[2022] ewca civ 123"
        corrected_citation = "[2022] EWCA Civ 123"
        year = "2022"
        URI = "#"
        is_neutral = "true"
        text = "[2022] ewca civ 123."
        replacement_entry = (citation_match, corrected_citation, year, URI, is_neutral)
        replaced_entry = replacer_caselaw(text, replacement_entry)
        assert corrected_citation in replaced_entry
        replacement_string = '<ref uk:type="case" href="{}" uk:isNeutral="{}" uk:canonical="{}" uk:year="{}" uk:origin="TNA">{}</ref>'.format(
            URI, is_neutral, corrected_citation, year, citation_match
        )
        assert replacement_string in replaced_entry


class TestLegislationReplacer(unittest.TestCase):
    """
    This class tests the replacement of the legislations within the text itself.
    """

    def test_citation_replacer(self):
        legislation_match = "Adoption and Children Act 2002"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2002/38"
        text = "In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption and Children Act 2002 requires the court, inter alia"
        canonical = "foo"
        replacement_entry = (legislation_match, href, canonical)
        replaced_entry = replacer_leg(text, replacement_entry)
        assert legislation_match in replaced_entry
        replacement_string = '<ref uk:type="legislation" href="http://www.legislation.gov.uk/ukpga/2002/38" uk:canonical="foo" uk:origin="TNA">Adoption and Children Act 2002</ref>'
        assert replacement_string in replaced_entry

        legislation_match = "Children and Families Act 2014"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2014/6/enacted"
        text = "In her first judgment on 31 January, the judge correctly directed herself as to the law, reminding herself that any application for expert evidence in children’s proceedings is governed by s.13 of the Children and Families Act 2014."
        canonical = "bar"
        replacement_entry = (legislation_match, href, canonical)
        replaced_entry = replacer_leg(text, replacement_entry)
        assert legislation_match in replaced_entry
        replacement_string = '<ref uk:type="legislation" href="http://www.legislation.gov.uk/ukpga/2014/6/enacted" uk:canonical="bar" uk:origin="TNA">Children and Families Act 2014</ref>'
        assert replacement_string in replaced_entry


class TestReplacerAbbr(unittest.TestCase):
    """Unit Tests for `replacer_abbr`"""

    def test_replacer_abbr(self):
        """
        Given a text string and a tuple of original string and abbreviation
            where the original string is contained in the text string
        When replacer_abbr is called with these
        Then a string is returned that looks like the original text string
            with the matching string enclosed by an <abbr> tag with the replacement
            string as the title attribute and TNA as the uk:origin attribute
        """
        text = "This game requires 12 GB of Random Access Memory"
        replacement_entry = ("Random Access Memory", "RAM")

        expected = (
            "This game requires 12 GB of "
            '<abbr title="RAM" uk:origin="TNA">'
            "Random Access Memory"
            "</abbr>"
        )
        assert replacer_abbr(text, replacement_entry) == expected
