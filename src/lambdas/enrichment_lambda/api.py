import json
import logging
from typing import Any

import requests
import urllib3
from requests.auth import HTTPBasicAuth

from utils.custom_types import APIEndpointBaseURL, DocumentAsXMLString

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def fetch_judgment(api_endpoint: APIEndpointBaseURL, query: str, username: str, password: str) -> DocumentAsXMLString:
    http = urllib3.PoolManager()
    url = f"{api_endpoint}judgment/{query}"
    headers = urllib3.make_headers(basic_auth=username + ":" + password)
    response = http.request("GET", url, headers=headers)

    if response.status != 200:
        message = (
            f"Failed to fetch judgment from {url}, status code: {response.status}, response: {response.data.decode()}"
        )
        LOGGER.error(message)
        raise RuntimeError(message)

    LOGGER.info("Successfully fetched judgment at %s", query)
    return DocumentAsXMLString(response.data.decode())


def lock_judgment(api_endpoint: APIEndpointBaseURL, query: str, username: str, password: str) -> None:
    http = urllib3.PoolManager()
    url = f"{api_endpoint}lock/{query}?unlock=3600"
    headers = urllib3.make_headers(basic_auth=username + ":" + password)
    response = http.request("PUT", url, headers=headers)

    if response.status != 201:
        message = (
            f"Failed to lock judgment from {url}, status code: {response.status}, response: {response.data.decode()}"
        )
        LOGGER.error(message)
        raise RuntimeError(message)

    LOGGER.info("Judgment locked successfully")


def patch_judgment(
    api_endpoint: APIEndpointBaseURL,
    document_uri: str,
    data: str,
    username: str,
    password: str,
) -> None:
    response = requests.patch(
        f"{api_endpoint}judgment/{document_uri}",
        auth=HTTPBasicAuth(username, password),
        data=data.encode(),
        params={"unlock": True},
        timeout=10,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        message = (
            f"Failed to patch judgment {document_uri}, status code: {response.status_code}, response: {response.text}"
        )
        LOGGER.error(message)
        raise RuntimeError(message) from exc


def read_message(message_dict: dict[Any, Any]) -> tuple[str, str]:
    json_body = json.dumps(message_dict)
    json_message = json.loads(json_body)
    message = json_message["Message"]
    message_read = json.loads(message)
    status = message_read["status"]
    uri_reference = message_read["uri_reference"]
    return status, uri_reference
