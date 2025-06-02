from collections import namedtuple
from typing import NewType

Abbreviation = namedtuple("Abbreviation", ["abb_match", "longform"])
# An abbreviation, and its long form.

Replacement = NewType("Replacement", tuple[str, str, str, str, bool])
# ('[2022] UKSC 3', '[2022] UKSC 3', '2022', 'https://caselaw.nationalarchives.gov.uk/uksc/2022/3', True)

ReplacementList = NewType("ReplacementList", list[Replacement])

Reference = list[tuple[tuple[int, int], str]]
# The first part is a span (from inter-character-position to another) and the second is the string found there

APIEndpointBaseURL = NewType("APIEndpointBaseURL", str)
""" A string representing the endpoint URL of an FCL Privileged API instance. """

XMLFragmentAsString = NewType("XMLFragmentAsString", str)
""" A string representation of some XML. """

DocumentAsXMLString = NewType("DocumentAsXMLString", str)
""" An entire document as a string representation of XML. """

DocumentAsXMLBytes = NewType("DocumentAsXMLBytes", bytes)
""" An entire document as a bytestring representation of XML. """
