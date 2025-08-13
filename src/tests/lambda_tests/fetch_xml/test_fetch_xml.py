import json
import logging
import os
from unittest import mock

import boto3
import pytest
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from moto import mock_aws

from lambdas.fetch_xml.index import (
    APIEndpointBaseURL,
    DocumentAsXMLString,
    check_lock_judgment_urllib,
    fetch_judgment_urllib,
    lock_judgment_urllib,
    process_event,
    upload_contents,
)

# Test data
TEST_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso>
    <judgment>
        <header>
            <p>Test judgment content</p>
        </header>
    </judgment>
</akomaNtoso>"""

TEST_SQS_MESSAGE = {
    "Message": json.dumps(
        {
            "status": "ready",
            "uri_reference": "test-judgment-123",
        },
    ),
}

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


@pytest.fixture
def api_client():
    return {
        "api_endpoint": APIEndpointBaseURL("https://test.example.com/"),
        "query": "test-judgment",
        "username": "test-user",
        "password": "test-pass",
    }


@mock.patch("urllib3.PoolManager")
def test_fetch_judgment_urllib_success(mock_pool_manager, api_client):
    mock_response = mock.Mock()
    mock_response.status = 200
    mock_response.data.decode.return_value = TEST_XML_CONTENT

    mock_pool_manager.return_value.request.return_value = mock_response

    result = fetch_judgment_urllib(
        api_client["api_endpoint"],
        api_client["query"],
        api_client["username"],
        api_client["password"],
    )
    assert result == TEST_XML_CONTENT


@mock.patch("urllib3.PoolManager")
def test_fetch_judgment_urllib_error(mock_pool_manager, api_client):
    mock_response = mock.Mock()
    mock_response.status = 404
    mock_response.data.decode.return_value = "Not Found"

    mock_pool_manager.return_value.request.return_value = mock_response

    with pytest.raises(RuntimeError) as exc_info:
        fetch_judgment_urllib(
            api_client["api_endpoint"],
            api_client["query"],
            api_client["username"],
            api_client["password"],
        )

    assert "Failed to fetch judgment" in str(exc_info.value)
    assert "404" in str(exc_info.value)
    assert "Not Found" in str(exc_info.value)


def test_lock_judgment_urllib_success(api_client):
    with mock.patch("urllib3.PoolManager") as mock_pool_manager:
        mock_response = mock.Mock()
        mock_response.status = 201
        mock_response.data.decode.return_value = "Locked successfully"

        mock_pool_manager.return_value.request.return_value = mock_response

        lock_judgment_urllib(
            api_client["api_endpoint"],
            api_client["query"],
            api_client["username"],
            api_client["password"],
        )
        mock_pool_manager.return_value.request.assert_called_once_with(
            "PUT",
            f"{api_client['api_endpoint']}lock/{api_client['query']}?unlock=3600",
            headers=mock.ANY,
        )


def test_lock_judgment_urllib_error(api_client):
    with mock.patch("urllib3.PoolManager") as mock_pool_manager:
        mock_response = mock.Mock()
        mock_response.status = 500
        mock_response.data.decode.return_value = "Internal Server Error"

        mock_pool_manager.return_value.request.return_value = mock_response

        with pytest.raises(RuntimeError) as exc_info:
            lock_judgment_urllib(
                api_client["api_endpoint"],
                api_client["query"],
                api_client["username"],
                api_client["password"],
            )

        assert "Failed to lock judgment" in str(exc_info.value)
        assert "500" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)


@mock.patch("urllib3.PoolManager")
def test_check_lock_judgment_urllib_error(mock_pool_manager, api_client):
    mock_response = mock.Mock()
    mock_response.status = 500
    mock_response.data.decode.return_value = "Internal Server Error"

    mock_pool_manager.return_value.request.return_value = mock_response

    with pytest.raises(RuntimeError) as exc_info:
        check_lock_judgment_urllib(
            api_client["api_endpoint"],
            api_client["query"],
            api_client["username"],
            api_client["password"],
        )

    assert "Failed to check lock status" in str(exc_info.value)
    assert "500" in str(exc_info.value)
    assert "Internal Server Error" in str(exc_info.value)


@mock.patch("urllib3.PoolManager")
def test_check_lock_judgment_urllib_not_locked(mock_pool_manager, api_client):
    mock_response = mock.Mock()
    mock_response.status = 200
    mock_response.data.decode.return_value = json.dumps({"status": "Unlocked"})

    mock_pool_manager.return_value.request.return_value = mock_response

    result = check_lock_judgment_urllib(
        api_client["api_endpoint"],
        api_client["query"],
        api_client["username"],
        api_client["password"],
    )
    assert not result


@mock.patch("urllib3.PoolManager")
def test_check_lock_judgment_urllib_locked(mock_pool_manager, api_client):
    mock_response = mock.Mock()
    mock_response.status = 200
    mock_response.data.decode.return_value = json.dumps({"status": "Locked"})

    mock_pool_manager.return_value.request.return_value = mock_response

    result = check_lock_judgment_urllib(
        api_client["api_endpoint"],
        api_client["query"],
        api_client["username"],
        api_client["password"],
    )
    assert result


@mock_aws
def test_upload_contents():
    # Set up S3 bucket
    bucket_name = "test-upload-bucket"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)

    # Upload content
    source_key = "test-document"
    content = DocumentAsXMLString("<test>content</test>")
    upload_contents(source_key, content, bucket_name)

    # Verify upload
    response = s3.get_object(
        Bucket=bucket_name,
        Key="test-document.xml",
    )
    uploaded_content = response["Body"].read().decode()
    assert uploaded_content == content


@pytest.fixture
def env_vars():
    with mock.patch.dict(
        os.environ,
        {
            "DEST_BUCKET_NAME": "test-bucket",
            "API_USERNAME": "test-user",
            "API_PASSWORD": "test-pass",
            "ENVIRONMENT": "staging",
        },
    ):
        yield


@pytest.fixture
def mock_sqs_record():
    record = mock.Mock(spec=SQSRecord)
    record.body = json.dumps(TEST_SQS_MESSAGE)
    return record


@mock_aws
@mock.patch("urllib3.PoolManager")
def test_process_event_success(mock_pool_manager, env_vars, mock_sqs_record, api_client):
    # Set up mock responses for all API calls
    mock_responses = {
        # Fetch judgment response
        f"{api_client['api_endpoint']}judgment/test-judgment-123": mock.Mock(
            status=200,
            data=TEST_XML_CONTENT.encode(),
        ),
        # Lock judgment response
        f"{api_client['api_endpoint']}lock/test-judgment-123?unlock=3600": mock.Mock(
            status=201,
            data=b"Locked successfully",
        ),
        # Check lock response
        f"{api_client['api_endpoint']}lock/test-judgment-123": mock.Mock(
            status=200,
            data=json.dumps({"status": "Locked"}).encode(),
        ),
    }

    def mock_request(method, url, headers=None, **kwargs):
        if url in mock_responses:
            return mock_responses[url]
        error = f"Unexpected URL: {url}"
        raise Exception(error)

    mock_pool_manager.return_value.request.side_effect = mock_request

    # Set up S3 bucket
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")

    # Run the process_event function
    process_event(
        mock_sqs_record,
        api_client["api_endpoint"],
        api_client["username"],
        api_client["password"],
        "test-bucket",
    )

    # Verify S3 upload
    response = s3.get_object(
        Bucket="test-bucket",
        Key="test-judgment-123.xml",
    )
    uploaded_content = response["Body"].read().decode()
    assert uploaded_content == TEST_XML_CONTENT

    # Verify all API calls were made
    expected_calls = [
        mock.call("GET", f"{api_client['api_endpoint']}judgment/test-judgment-123", headers=mock.ANY),
        mock.call("PUT", f"{api_client['api_endpoint']}lock/test-judgment-123?unlock=3600", headers=mock.ANY),
        mock.call("GET", f"{api_client['api_endpoint']}lock/test-judgment-123", headers=mock.ANY),
    ]
    actual_calls = mock_pool_manager.return_value.request.call_args_list
    assert len(actual_calls) == len(expected_calls)
    for expected, actual in zip(expected_calls, actual_calls, strict=False):
        assert expected.args[0] == actual[0][0]  # Compare HTTP method
        assert expected.args[1] == actual[0][1]  # Compare URL
