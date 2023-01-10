"""
Helper functions for JEP.
"""


import bs4 as BeautifulSoup
import pandas as pd


def load_patterns(conn):
    """
    Write patterns file
    :param conn: Database connection
    """
    rules_manifest = pd.read_sql("""SELECT * FROM manifest""", conn)
    patterns = rules_manifest["pattern"].tolist()
    with open("rules/citation_patterns.jsonl", "w+") as patterns_file:
        for pattern in patterns:
            patterns_file.write(pattern + "\n")


def parse_file(file_data):
    """
    Parse XML file. Only get text within content elements
    :param file_data: XML file
    """
    soup = BeautifulSoup.BeautifulSoup(str(file_data), "xml")
    judgment_content = soup.find_all("content")
    judgment_content_text = " ".join(
        [content.text.strip() for content in judgment_content]
    )
    return judgment_content_text
