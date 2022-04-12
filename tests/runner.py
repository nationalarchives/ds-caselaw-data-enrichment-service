# tests/runner.py
import unittest
from caselaw_extraction_tests.test_case_citations import TestCorrectionStrategy, TestCitationProcessor, TestCitationReplacer
from abbreviation_extraction_tests.test_abbreviations import TestAbbrevationMatcher, TestAbbrevationReplacer
from legislation_extraction_tests.test_legislation_citations import TestLegislationProcessor, TestLegislationReplacer
from test_xml_parser import TestXmlParser

# initialize the test suite

XMLParserSuite = unittest.TestLoader().loadTestsFromTestCase(TestXmlParser)
CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationReplacer)
AbbreviationMatcher = unittest.TestLoader().loadTestsFromTestCase(TestAbbrevationMatcher)
AbbreviationReplacer = unittest.TestLoader().loadTestsFromTestCase(TestAbbrevationReplacer)
LegislationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestLegislationProcessor)
LegislationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestLegislationReplacer)

suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite, CitationReplacerSuite, XMLParserSuite, AbbreviationMatcher, AbbreviationReplacer, LegislationProcessorSuite, LegislationReplacerSuite])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)