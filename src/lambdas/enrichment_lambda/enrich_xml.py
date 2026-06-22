"""Module for enriching XML files with caselaw, legislation, and abbreviation replacements, as well as oblique references and metadata."""

import logging

from lambdas.enrichment_lambda.steps import (
    add_timestamp_and_engine_version,
    determine_abbreviation_replacements,
    determine_caselaw_replacements,
    determine_legislation_replacements,
    enrich_oblique_references,
    make_post_header_replacements,
    make_replacements_input,
    replace_legislation_provisions,
)
from utils.custom_types import DocumentAsXMLString
from utils.helper import parse_file

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def enrich_xml(xml: str, pattern_list: list[dict], enrichment_version: str = "7.4.0") -> str:
    """Orchestrate the enrichment pipeline: replacements, oblique references, legislation provisions, and metadata."""
    # all run on original XML sequentially, so that replacements are applied before enrichment
    parsed_xml = parse_file(DocumentAsXMLString(xml))
    caselaw_replacements = determine_caselaw_replacements(parsed_xml, pattern_list)

    legislation_replacements = determine_legislation_replacements(parsed_xml)
    abbreviation_replacements = determine_abbreviation_replacements(parsed_xml)

    # create a single JSON string of all replacements to pass to the replacer
    replacement_file_content = make_replacements_input(
        caselaw_replacements,
        abbreviation_replacements,
        legislation_replacements,
    )

    # appply the basic replacements to the XML, before enriching with oblique references and legislation provisions
    xml_with_replacements = make_post_header_replacements(DocumentAsXMLString(xml), replacement_file_content)

    # then enrich with oblique references and legislation provisions
    xml_with_oblique_references = enrich_oblique_references(xml_with_replacements)
    fully_enriched_xml = replace_legislation_provisions(xml_with_oblique_references)

    # add timestamp and engine version to the fully enriched XML
    fully_enriched_xml_with_timestamp = add_timestamp_and_engine_version(
        fully_enriched_xml,
        enrichment_version,
    )
    return fully_enriched_xml_with_timestamp
