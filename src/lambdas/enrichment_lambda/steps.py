import json
import logging

import boto3
import spacy
from bs4 import BeautifulSoup

from database import db_connection
from enrichment.abbreviation_extraction.abbreviations_matcher import abb_pipeline
from enrichment.caselaw_extraction.caselaw_matcher import case_pipeline
from enrichment.legislation_extraction.legislation_matcher_hybrid import leg_pipeline
from enrichment.legislation_provisions_extraction.legislation_provisions import provisions_pipeline
from enrichment.replacer.second_stage_replacer import replace_references_by_paragraph
from utils.custom_types import DocumentAsXMLString
from utils.initialise_db import init_db_connection

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def determine_abbreviation_replacements(file_content: str):
    nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"])
    nlp.max_length = 2500000
    return abb_pipeline(file_content, nlp)


def determine_caselaw_replacements(file_content: str, rules_bucket: str, rules_key: str):
    db_conn = init_db_connection()
    try:
        nlp = _init_caselaw_nlp(rules_bucket, rules_key)
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


def replace_legislation_provisions(xml: str) -> str:
    resolved_refs = provisions_pipeline(DocumentAsXMLString(xml))
    if not resolved_refs:
        return xml
    soup = BeautifulSoup(xml, "xml")
    return str(replace_references_by_paragraph(soup, resolved_refs))


def _init_caselaw_nlp(rules_bucket: str, rules_key: str):
    nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"])
    nlp.max_length = 5000000

    s3 = boto3.client("s3")
    patterns_resp = s3.get_object(Bucket=rules_bucket, Key=rules_key)
    patterns = patterns_resp["Body"]
    pattern_list = [json.loads(line) for line in patterns.iter_lines()]

    citation_ruler = nlp.add_pipe("entity_ruler")
    citation_ruler.add_patterns(pattern_list)
    return nlp
