# tests/runner.py
import unittest
from caselaw_extraction_tests.test_case_citations import TestCorrectionStrategy, TestCitationProcessor, TestCitationReplacer
from abbreviation_extraction_tests.test_abbreviations import TestAbbrevationMatcher, TestAbbrevationReplacer
from legislation_extraction_tests.test_legislation_citations import TestLegislationProcessor, TestLegislationReplacer
from test_xml_parser import TestXmlParser
from legislation_provision_extraction_tests import TestLegislationProvisionProcessor
from oblique_reference_extraction_tests import TestObliqueReferencesProcessor

"""
Test suite for the project. Loads and runs all tests.
"""

# initialize the test suite

XMLParserSuite = unittest.TestLoader().loadTestsFromTestCase(TestXmlParser)
CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationReplacer)
AbbreviationMatcher = unittest.TestLoader().loadTestsFromTestCase(TestAbbrevationMatcher)
AbbreviationReplacer = unittest.TestLoader().loadTestsFromTestCase(TestAbbrevationReplacer)
LegislationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestLegislationProcessor)
LegislationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestLegislationReplacer)
LegislationProvisionSuite = unittest.TestLoader().loadTestsFromTestCase(TestLegislationProvisionProcessor)
ObliqueReferenceSuite = unittest.TestLoader().loadTestsFromTestCase(TestObliqueReferencesProcessor)

suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite, CitationReplacerSuite, XMLParserSuite, AbbreviationMatcher, AbbreviationReplacer, \
    LegislationProcessorSuite, LegislationReplacerSuite, LegislationProvisionSuite, ObliqueReferenceSuite])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)