from typing import NamedTuple, NewType


class Replacement[T](NamedTuple):
    match: str
    data: T


class AbbreviationData(NamedTuple):
    longform: str


class CaselawData(NamedTuple):
    canonical: str
    year: str
    url: str
    is_ncn: bool


class LegislationData(NamedTuple):
    url: str
    canonical: str


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
