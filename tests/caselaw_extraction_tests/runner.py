# tests/runner.py
import unittest
from test_case_citations import TestCitationProcessor, TestCorrectionStrategy, TestCitationReplacer
from test_xml_parser import TestXmlParser

# initialize the test suite

XMLParserSuite = unittest.TestLoader().loadTestsFromTestCase(TestXmlParser)
CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationReplacer)
suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite, CitationReplacerSuite, XMLParserSuite])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)