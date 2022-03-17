# tests/runner.py
import unittest
from test_case_citations import TestCitationProcessor, TestCorrectionStrategy, TestCitationReplacer

# initialize the test suite

CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
CitationReplacerSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationReplacer)
suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite, CitationReplacerSuite])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)