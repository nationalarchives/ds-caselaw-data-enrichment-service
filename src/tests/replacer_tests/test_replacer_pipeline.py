import unittest

from replacer.replacer_pipeline import (
    fixed_year,
    replacer_abbr,
    replacer_caselaw,
    replacer_leg,
)


class TestCitationReplacer(unittest.TestCase):
    """
    This class tests the replacement of the citations within the text itself. This comes from shared.replacer.py
    """

    def test_citation_replacer_1(self):
        citation_match = "[2025] 1 All E.R. 123"  # incorrect citation
        corrected_citation = "[2025] 1 All ER 123"  # in practice, returned via the citation matcher
        year = "2025"
        uri = "#"
        is_neutral = "true"
        text = "<z>In the judgment the incorrect citation is [2025] 1 All E.R. 123. <table uk:widths='1.38in 1.05in 0.91in 0.98in 0.98in 0.95in'></table></z>"
        replacement_entry = (citation_match, corrected_citation, year, uri, is_neutral)
        assert (
            replacer_caselaw(text, replacement_entry)
            == '<z>In the judgment the incorrect citation is <ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="[2025] 1 All ER 123" uk:year="2025" uk:origin="TNA">[2025] 1 All E.R. 123</ref>. <table uk:widths="1.38in 1.05in 0.91in 0.98in 0.98in 0.95in"/></z>'
        )

    def test_citation_replacer_2(self):
        citation_match = "[2022] UKET 789123_2012"
        corrected_citation = "[2022] UKET 789123/2012"
        year = "2022"
        uri = "#"
        is_neutral = "true"
        text = "<z>This citation that needs to be changed is [2022] UKET 789123_2012 which discussed...</z>"
        replacement_entry = (citation_match, corrected_citation, year, uri, is_neutral)
        assert (
            replacer_caselaw(text, replacement_entry)
            == '<z>This citation that needs to be changed is <ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="[2022] UKET 789123/2012" uk:year="2022" uk:origin="TNA">[2022] UKET 789123_2012</ref> which discussed...</z>'
        )

    def test_citation_replacer_3_no_year(self):
        """Note that this test does not have a year, so there is no uk:year attribute, unlike the others"""
        citation_match = "LR 1 A&E 123"
        corrected_citation = "LR 1 AE 123"
        year = "No Year"
        text = "<z>LR 1 A&amp;E 123 refers to...</z>"
        uri = "#"
        is_neutral = "true"
        replacement_entry = (citation_match, corrected_citation, year, uri, is_neutral)
        assert (
            replacer_caselaw(text, replacement_entry)
            == '<z><ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="LR 1 AE 123" uk:origin="TNA">LR 1 A&amp;E 123</ref> refers to...</z>'
        )

    def test_citation_replacer_4(self):
        citation_match = "(2022) EWHC 123 (Mercantile)"
        corrected_citation = "[2022] EWHC 123 (Mercantile)"
        year = "2022"
        uri = "#"
        is_neutral = "true"
        text = "<z>I defer to the judgment in (2022) EWHC 123 (Mercantile).</z>"
        replacement_entry = (citation_match, corrected_citation, year, uri, is_neutral)
        assert (
            replacer_caselaw(text, replacement_entry)
            == '<z>I defer to the judgment in <ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="[2022] EWHC 123 (Mercantile)" uk:year="2022" uk:origin="TNA">(2022) EWHC 123 (Mercantile)</ref>.</z>'
        )

    def test_citation_replacer_5(self):
        citation_match = "[2022] ewca civ 123"
        corrected_citation = "[2022] EWCA Civ 123"
        year = "2022"
        uri = "#"
        is_neutral = "true"
        text = "<z>[2022] ewca civ 123.</z>"
        replacement_entry = (citation_match, corrected_citation, year, uri, is_neutral)
        assert (
            replacer_caselaw(text, replacement_entry)
            == '<z><ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="case" href="#" uk:isNeutral="true" uk:canonical="[2022] EWCA Civ 123" uk:year="2022" uk:origin="TNA">[2022] ewca civ 123</ref>.</z>'
        )


class TestLegislationReplacer(unittest.TestCase):
    """
    This class tests the replacement of the citations within the text itself. This comes from shared.replacer.py
    """

    def test_citation_replacer_1(self):
        legislation_match = "Adoption and Children Act 2002"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2002/38"
        text = "<z>In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the Adoption and Children Act 2002 requires the court, inter alia</z>"
        canonical = "foo"
        replacement_entry = (legislation_match, href, canonical)
        assert (
            replacer_leg(text, replacement_entry)
            == '<z>In their skeleton argument in support of the first ground, Mr Goodwin and Mr Redmond remind the court that the welfare checklist in s.1(4) of the <ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="legislation" href="http://www.legislation.gov.uk/ukpga/2002/38" uk:canonical="foo" uk:origin="TNA">Adoption and Children Act 2002</ref> requires the court, inter alia</z>'
        )

    def test_citation_replacer_2(self):
        legislation_match = "Children and Families Act 2014"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2014/6/enacted"
        text = "<z>In her first judgment on 31 January, the judge correctly directed herself as to the law, reminding herself that any application for expert evidence in children’s proceedings is governed by s.13 of the Children and Families Act 2014.</z>"
        canonical = "bar"
        replacement_entry = (legislation_match, href, canonical)
        assert (
            replacer_leg(text, replacement_entry)
            == '<z>In her first judgment on 31 January, the judge correctly directed herself as to the law, reminding herself that any application for expert evidence in children&#8217;s proceedings is governed by s.13 of the <ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="legislation" href="http://www.legislation.gov.uk/ukpga/2014/6/enacted" uk:canonical="bar" uk:origin="TNA">Children and Families Act 2014</ref>.</z>'
        )

    def test_citation_replacer_2_no_enacted(self):
        legislation_match = "Children and Families Act 2014"  # matched legislation
        href = "http://www.legislation.gov.uk/ukpga/2014/6"
        text = "<z>In her first judgment on 31 January, the judge correctly directed herself as to the law, reminding herself that any application for expert evidence in children’s proceedings is governed by s.13 of the Children and Families Act 2014.</z>"
        canonical = "bar"
        replacement_entry = (legislation_match, href, canonical)
        assert (
            replacer_leg(text, replacement_entry)
            == '<z>In her first judgment on 31 January, the judge correctly directed herself as to the law, reminding herself that any application for expert evidence in children&#8217;s proceedings is governed by s.13 of the <ref xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" uk:type="legislation" href="http://www.legislation.gov.uk/ukpga/2014/6" uk:canonical="bar" uk:origin="TNA">Children and Families Act 2014</ref>.</z>'
        )


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
        text = "<z xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn'>This game requires 12 GB of Random Access Memory</z>"
        replacement_entry = ("Random Access Memory", "RAM")

        expected = '<z xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">This game requires 12 GB of <abbr title="RAM" uk:origin="TNA">Random Access Memory</abbr></z>'
        assert replacer_abbr(text, replacement_entry) == expected


class TestFixedYear(unittest.TestCase):
    def test_no_year(self):
        assert fixed_year(None) is None

    def test_empty_year(self):
        assert fixed_year("") is None

    def test_gibberish_year(self):
        assert fixed_year("xxx") is None

    def test_real_year(self):
        assert fixed_year("1969") == "1969"

    def test_mixed_year(self):
        """This shouldn't be used anywhere, it's merely documenting the behaviour added whilst fixing the No Year issue"""
        assert fixed_year("In the summer of '69") == "69"
