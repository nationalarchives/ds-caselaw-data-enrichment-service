import json
from unittest.mock import Mock, patch

import pytest
import requests

from lambdas.enrichment_lambda import api


@patch("lambdas.enrichment_lambda.api.urllib3.PoolManager")
def test_fetch_judgment_success(mock_pool_manager):
    response = Mock()
    response.status = 200
    response.data.decode.return_value = "<xml/>"
    mock_pool_manager.return_value.request.return_value = response

    result = api.fetch_judgment("https://api.example/", "uksc/2024/1", "user", "pass")

    assert result == "<xml/>"


@patch("lambdas.enrichment_lambda.api.urllib3.PoolManager")
def test_fetch_judgment_non_200_raises(mock_pool_manager):
    response = Mock()
    response.status = 404
    response.data.decode.return_value = "missing"
    mock_pool_manager.return_value.request.return_value = response

    with pytest.raises(RuntimeError, match="Failed to fetch judgment"):
        api.fetch_judgment("https://api.example/", "not-found", "user", "pass")


@patch("lambdas.enrichment_lambda.api.urllib3.PoolManager")
def test_lock_judgment_non_201_raises(mock_pool_manager):
    response = Mock()
    response.status = 500
    response.data.decode.return_value = "error"
    mock_pool_manager.return_value.request.return_value = response

    with pytest.raises(RuntimeError, match="Failed to lock judgment"):
        api.lock_judgment("https://api.example/", "uksc/2024/1", "user", "pass")


@patch("lambdas.enrichment_lambda.api.urllib3.PoolManager")
def test_unlock_judgment_non_204_or_200_raises(mock_pool_manager):
    response = Mock()
    response.status = 500
    response.data.decode.return_value = "error"
    mock_pool_manager.return_value.request.return_value = response

    with pytest.raises(RuntimeError, match="Failed to unlock judgment"):
        api.unlock_judgment("https://api.example/", "uksc/2024/1", "user", "pass")


@patch("lambdas.enrichment_lambda.api.requests.patch")
def test_patch_judgment_http_error_raises_runtime_error(mock_patch):
    response = Mock()
    response.status_code = 500
    response.text = "patch-failed"
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("bad status")
    mock_patch.return_value = response

    with pytest.raises(RuntimeError, match="Failed to patch judgment"):
        api.patch_judgment("https://api.example/", "uksc/2024/1", "<xml/>", "user", "pass")


def test_read_message_parses_nested_message_body():
    payload = {
        "Message": json.dumps(
            {
                "status": "ready",
                "uri_reference": "uksc/2024/1",
            },
        ),
    }

    status, uri_reference = api.read_message(payload)

    assert status == "ready"
    assert uri_reference == "uksc/2024/1"
