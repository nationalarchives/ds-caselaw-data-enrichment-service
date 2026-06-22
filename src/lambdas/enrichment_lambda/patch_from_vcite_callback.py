import logging
import urllib.parse
from typing import Any

import boto3
from lxml import etree

from lambdas.enrichment_lambda.api import patch_judgment
from utils.custom_types import APIEndpointBaseURL

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def patch_from_vcite_callback(
    record: dict[str, Any],
    api_endpoint: APIEndpointBaseURL,
    api_username: str,
    api_password: str,
) -> None:
    """Retrieve XML from S3 vCite callback bucket, canonicalize, and patch to API."""
    s3_client = boto3.client("s3")
    source_bucket = record["s3"]["bucket"]["name"]
    source_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"], encoding="utf-8")

    LOGGER.info("Processing vCite callback object: %s/%s", source_bucket, source_key)
    file_content = s3_client.get_object(Bucket=source_bucket, Key=source_key)["Body"].read()

    tree = etree.fromstring(file_content)
    canonical_xml = etree.tostring(tree, method="c14n").decode("utf-8")
    document_uri = source_key.replace(".xml", "")

    patch_judgment(api_endpoint, document_uri, canonical_xml, api_username, api_password)
    LOGGER.info("Patched vCite callback XML to API for: %s", document_uri)
