"""
Helper functions for JEP.
"""

import re

import bs4 as BeautifulSoup

from utils.types import DocumentAsXMLString


def parse_file(file_data: DocumentAsXMLString) -> str:
    """
    Parse XML file. Only get text within content elements
    :param file_data: XML file
    :returns judgement_content_text: all content elements in judgment
    """
    soup = BeautifulSoup.BeautifulSoup(str(file_data), "xml")
    judgment_content = soup.find_all(re.compile(r"(content|intro|wrapUp)"))
    judgment_content_text = " ".join(
        [content.text.strip() for content in judgment_content],
    )
    return judgment_content_text
