# tests/runner.py
import unittest
from caselaw_extraction_tests.test_case_citations import TestCitationProcessor, TestCorrectionStrategy, TestCitationReplacer
from test_xml_parser import TestXmlParser
from tests.abbreviation_extraction_tests.test_abbreviations import TestAbbrevationMatcher, TestAbbrevationReplacer

# initialize the test suite

XMLParserSuite = unittest.TestLoader().loadTestsFromTestCase(TestXmlParser)
CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationReplacer)
AbbreviationMatcher = unittest.TestLoader().loadTestsFromTestCase(TestAbbrevationMatcher)
AbbreviationReplacer = unittest.TestLoader().loadTestsFromTestCase(TestAbbrevationReplacer)
suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite, CitationReplacerSuite, XMLParserSuite, AbbreviationMatcher, AbbreviationReplacer])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)