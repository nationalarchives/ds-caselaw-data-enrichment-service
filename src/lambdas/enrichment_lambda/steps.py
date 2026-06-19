import datetime
import json
import logging

import lxml
import spacy
from bs4 import BeautifulSoup

from database import db_connection
from enrichment.abbreviation_extraction.abbreviations_matcher import abb_pipeline
from enrichment.caselaw_extraction.caselaw_matcher import case_pipeline
from enrichment.legislation_extraction.legislation_matcher_hybrid import leg_pipeline
from enrichment.legislation_provisions_extraction.legislation_provisions import provisions_pipeline
from enrichment.oblique_references.oblique_references import (
    get_oblique_reference_replacements_by_paragraph,
)
from enrichment.replacer.make_replacements import (
    apply_replacements,
    sanitize_judgment,
    split_text_by_closing_header_tag,
)
from enrichment.replacer.second_stage_replacer import replace_references_by_paragraph
from utils.custom_types import DocumentAsXMLString
from utils.initialise_db import init_db_connection

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class SourceXMLMissingElement(RuntimeError):
    """The provided XML document is missing an expected element, and we are choosing to fail."""


def determine_abbreviation_replacements(file_content: str):
    nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"])
    nlp.max_length = 2500000
    return abb_pipeline(file_content, nlp)


def determine_caselaw_replacements(file_content: str, pattern_list: list[dict]):
    db_conn = init_db_connection()
    try:
        nlp = _init_caselaw_nlp(pattern_list)
        LOGGER.info("Loaded caselaw NLP model")
        doc = nlp(file_content)
        replacements = case_pipeline(doc, db_conn)
        LOGGER.info("Caselaw replacements identified: %s", len(replacements))
        return replacements
    finally:
        db_connection.close_connection(db_conn)


def determine_legislation_replacements(file_content: str):
    db_conn = init_db_connection()
    try:
        nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"])
        nlp.max_length = 2500000
        doc = nlp(file_content)
        leg_titles = db_connection.get_legtitles(db_conn)
        replacements = leg_pipeline(leg_titles, nlp, doc, db_conn)
        LOGGER.info("Legislation replacements identified: %s", len(replacements))
        return replacements
    finally:
        db_connection.close_connection(db_conn)


def make_replacements_input(caselaw_replacements, abbreviation_replacements, legislation_replacements) -> str:
    """
    Serialise replacement tuples into the line-delimited JSON format expected by the replacer.
    """
    tuple_file = ""
    for i in caselaw_replacements:
        tuple_file += json.dumps({f"{type(i).__name__}": list(i)}) + "\n"
    for i in abbreviation_replacements:
        tuple_file += json.dumps({f"{type(i).__name__}": list(i)}) + "\n"
    for i in legislation_replacements:
        tuple_file += json.dumps({f"{type(i).__name__}": list(i)}) + "\n"
    return tuple_file


def replace_legislation_provisions(xml: DocumentAsXMLString) -> DocumentAsXMLString:
    resolved_refs = provisions_pipeline(xml)

    if resolved_refs:
        soup = BeautifulSoup(xml, "xml")
        output_file_data = replace_references_by_paragraph(soup, resolved_refs)
        return DocumentAsXMLString(str(output_file_data))
    return xml


def add_timestamp_and_engine_version(
    file_data: DocumentAsXMLString,
    enrichment_version: str = "7.4.0",
) -> DocumentAsXMLString:
    """
    Add today's timestamp and version at time of enrichment
    """
    soup = BeautifulSoup(file_data, "xml")
    today = datetime.datetime.now(tz=datetime.UTC)
    today_str = today.strftime("%Y-%m-%dT%H:%M:%S")
    enriched_date = soup.new_tag(f'FRBRdate date="{today_str}" name="tna-enriched"')
    enrichment_version_tag = soup.new_tag(
        "uk:tna-enrichment-engine",
        attrs={"xmlns:uk": "https://caselaw.nationalarchives.gov.uk/akn"},
    )
    enrichment_version_tag.string = enrichment_version
    if not soup.proprietary:
        msg = "This document does not have a <proprietary> element."
        raise SourceXMLMissingElement(msg)

    soup.proprietary.append(enrichment_version_tag)

    if not soup.FRBRManifestation or not soup.FRBRManifestation.FRBRdate:
        msg = "This document does not already have a manifestation date."
        raise SourceXMLMissingElement(msg)

    soup.FRBRManifestation.FRBRdate.insert_after(enriched_date)

    return DocumentAsXMLString(str(soup))


def _init_caselaw_nlp(pattern_list: list[dict]) -> spacy.language.Language:
    nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"])
    nlp.max_length = 5000000

    citation_ruler = nlp.add_pipe("entity_ruler")
    citation_ruler.add_patterns(pattern_list)
    return nlp


def enrich_oblique_references(file_content: DocumentAsXMLString) -> DocumentAsXMLString:
    """
    Determines oblique references in the file_content and then returns
        an enriched file content with the replacements applied
    :param file_content: original file content
    :return: updated file content with enriched oblique references
    """
    oblique_reference_replacements = get_oblique_reference_replacements_by_paragraph(file_content)
    if not oblique_reference_replacements:
        return file_content
    soup = BeautifulSoup(file_content, "xml")
    return replace_references_by_paragraph(soup, oblique_reference_replacements)


def make_post_header_replacements(
    original_content: DocumentAsXMLString,
    replacement_patterns: str,
) -> DocumentAsXMLString:
    """
    Replaces the content following a closing header tag in a legal document with new content.
    If there is no closing header tag, then we replace the full content.

    Note:
    - This function assumes a specific structure of the legal document with closing header tags.

    Args:
        original_content (str): The original content of the legal document
        replacement_patterns (str): The line separated replacement patterns

    Returns:
        str: The modified legal document content with the replacement applied.
    """
    cleaned_file_content = sanitize_judgment(original_content)

    pre_header, end_header_tag, post_header = split_text_by_closing_header_tag(cleaned_file_content)

    replaced_post_header_content = apply_replacements(post_header, replacement_patterns)
    LOGGER.info("Got post-header replacement text content")

    full_replaced_text_content = pre_header + end_header_tag + replaced_post_header_content

    # raises an lxml.etree.XMLSyntaxError if the output is not valid XML
    lxml.etree.fromstring(full_replaced_text_content.encode("utf-8"))

    return DocumentAsXMLString(full_replaced_text_content)
