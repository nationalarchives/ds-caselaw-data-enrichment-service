# tests/runner.py
import unittest
from test_case_citations import TestCitationProcessor, TestCorrectionStrategy, TestCitationReplacer
from test_xml_parser import TestXmlParser

# initialize the test suite

CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationReplacer)
XMLParserSuite = unittest.TestLoader().loadTestsFromTestCase(TestXmlParser)
suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite, CitationReplacerSuite, XMLParserSuite])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)