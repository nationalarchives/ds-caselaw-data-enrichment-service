# tests/runner.py
import unittest
from test_case_citations import TestCitationProcessor, TestCitationMatcher

# initialize the test suite

suite1 = unittest.TestLoader().loadTestsFromTestCase(TestCitationMatcher)
suite2 = unittest.TestLoader().loadTestsFromTestCase(TestCitationProcessor)
suite = unittest.TestSuite([suite1, suite2])

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)