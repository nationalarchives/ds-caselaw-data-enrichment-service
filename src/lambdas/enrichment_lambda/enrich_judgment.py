"""Module for enriching judgments by fetching them from the API, enriching them, and patching them back."""

import logging

import boto3

from lambdas.enrichment_lambda.api import fetch_judgment, lock_judgment, patch_judgment
from lambdas.enrichment_lambda.enrich_xml import enrich_xml
from utils.custom_types import APIEndpointBaseURL

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def enrich_judgment(
    uri_reference: str,
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
    pattern_list: list[dict],
    vcite_enabled: bool = False,
    vcite_bucket: str = "",
) -> None:
    LOGGER.info("Enriching judgment: %s", uri_reference)

    LOGGER.info("Locking judgment: %s", uri_reference)
    lock_judgment(api_endpoint, uri_reference, api_username, api_password)

    LOGGER.info("Fetching judgment from API endpoint: %s", api_endpoint)
    xml_content = fetch_judgment(api_endpoint, uri_reference, api_username, api_password)

    LOGGER.info("Enriching judgment content for: %s", uri_reference)
    enriched_xml = enrich_xml(xml_content, pattern_list, enrichment_version="7.4.0")

    if vcite_enabled:
        # May delete this block if we don't want to support vCite callback events in the enrichment lambda
        source_key = f"{uri_reference}.xml"
        LOGGER.info("vCite is on; uploading XML content to vCite input bucket: %s/%s", vcite_bucket, source_key)
        s3 = boto3.resource("s3")
        s3.Object(vcite_bucket, source_key).put(Body=xml_content.encode("utf-8"))
        LOGGER.info("Uploaded to vCite input for: %s", uri_reference)
    else:
        LOGGER.info("Patching enriched judgment back to API endpoint: %s", api_endpoint)
        patch_judgment(api_endpoint, uri_reference, enriched_xml, api_username, api_password)
        LOGGER.info("Successfully enriched and patched: %s", uri_reference)
