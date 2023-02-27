# tests/runner.py
import unittest

from abbreviation_extraction_tests.test_abbreviations import (
    TestAbbrevationMatcher,
    TestAbbrevationReplacer,
)
from caselaw_extraction_tests.test_case_citations import (
    TestCitationProcessor,
    TestCitationReplacer,
    TestCorrectionStrategy,
)
from legislation_extraction_tests.test_legislation_citations import (
    TestLegislationProcessor,
    TestLegislationReplacer,
)
from legislation_provision_extraction_tests.test_legislation_provisions import (
    TestLegislationProvisionProcessor,
)
from oblique_reference_extraction_tests.test_oblique_references import (
    TestDetectReference,
    TestGetReplacements,
)
from test_xml_parser import TestXmlParser

"""
Test suite for the project. Loads and runs all tests.
"""

# initialize the test suite

XMLParserSuite = unittest.TestLoader().loadTestsFromTestCase(TestXmlParser)
CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(
    TestCorrectionStrategy
)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(
    TestCitationProcessor
)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(
    TestCitationReplacer
)
AbbreviationMatcher = unittest.TestLoader().loadTestsFromTestCase(
    TestAbbrevationMatcher
)
AbbreviationReplacer = unittest.TestLoader().loadTestsFromTestCase(
    TestAbbrevationReplacer
)
LegislationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(
    TestLegislationProcessor
)
LegislationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(
    TestLegislationReplacer
)
LegislationProvisionSuite = unittest.TestLoader().loadTestsFromTestCase(
    TestLegislationProvisionProcessor
)
DetectReferenceSuite = unittest.TestLoader().loadTestsFromTestCase(TestDetectReference)
GetReplacementsSuite = unittest.TestLoader().loadTestsFromTestCase(TestGetReplacements)

suite = unittest.TestSuite(
    [
        CorrectionStrategySuite,
        CitationProcessorSuite,
        CitationReplacerSuite,
        XMLParserSuite,
        AbbreviationMatcher,
        AbbreviationReplacer,
        LegislationProcessorSuite,
        LegislationReplacerSuite,
        LegislationProvisionSuite,
        DetectReferenceSuite,
        GetReplacementsSuite,
    ]
)

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
