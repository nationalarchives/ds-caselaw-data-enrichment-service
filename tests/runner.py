# tests/runner.py
import unittest
from test_case_citations import TestCitationProcessor, TestCorrectionStrategy

# initialize the test suite

CorrectionStrategySuite = unittest.TestLoader().loadTestsFromTestCase(TestCorrectionStrategy)
CitationProcessorSuite = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
suite = unittest.TestSuite([CorrectionStrategySuite, CitationProcessorSuite])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)