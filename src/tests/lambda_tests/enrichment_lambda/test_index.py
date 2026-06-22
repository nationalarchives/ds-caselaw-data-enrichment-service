import json
from unittest.mock import patch

import boto3
from moto import mock_aws

from lambdas.enrichment_lambda import index
from utils.custom_types import APIEndpointBaseURL


def _sqs_record(body: str, event_value: str | None = None) -> dict:
    record = {
        "messageId": "1",
        "receiptHandle": "rh",
        "body": body,
        "attributes": {
            "ApproximateReceiveCount": "1",
            "SentTimestamp": "0",
            "SenderId": "abc",
            "ApproximateFirstReceiveTimestamp": "0",
        },
        "messageAttributes": {},
        "md5OfBody": "x",
        "eventSource": "aws:sqs",
        "eventSourceARN": "arn:aws:sqs:eu-west-2:123456789012:test",
        "awsRegion": "eu-west-2",
    }
    if event_value is not None:
        record["Event"] = event_value
    return record


def test_make_replacements_input_serializes_all_replacement_lists():
    caselaw_replacements = [("A", "B", "C", "D", True)]
    abbreviation_replacements = [("E", "F", "G", "H", False)]
    legislation_replacements = [("I", "J", "K", "L", True)]

    payload = index.make_replacements_input(
        caselaw_replacements,
        abbreviation_replacements,
        legislation_replacements,
    )

    lines = [json.loads(line) for line in payload.strip().splitlines()]

    assert lines == [
        {"tuple": ["A", "B", "C", "D", True]},
        {"tuple": ["E", "F", "G", "H", False]},
        {"tuple": ["I", "J", "K", "L", True]},
    ]


@patch("lambdas.enrichment_lambda.index.patch_judgment")
@patch("lambdas.enrichment_lambda.index.enrich_xml_file", return_value="<enriched/>")
@patch("lambdas.enrichment_lambda.index.lock_judgment")
@patch("lambdas.enrichment_lambda.index.fetch_judgment", return_value="<xml/>")
def test_enrich_judgment_happy_path(
    mock_fetch,
    mock_lock,
    mock_enrich,
    mock_patch,
):
    uri_reference = "uksc/2024/1"
    endpoint = APIEndpointBaseURL("https://api.example/")

    index.enrich_judgment(
        uri_reference,
        endpoint,
        "user",
        "pass",
        pattern_list=[
            {"pattern": "value"},
            {"pattern2": "value2"},
        ],
    )

    mock_fetch.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")
    mock_lock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")
    mock_enrich.assert_called_once_with(
        "<xml/>",
        [
            {"pattern": "value"},
            {"pattern2": "value2"},
        ],
        enrichment_version="7.4.0",
    )
    mock_patch.assert_called_once_with(endpoint, "uksc/2024/1", "<enriched/>", "user", "pass")


@mock_aws
@patch("lambdas.enrichment_lambda.index._process_sqs_enrichment_event")
@patch("lambdas.enrichment_lambda.index._read_vcite_toggle", return_value="off")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_uses_staging_endpoint_and_skips_s3_test_event(
    mock_validate_env,
    _mock_vcite_toggle,
    mock_process_sqs,
):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "staging",
        "RULES_FILE_BUCKET": "rules-bucket",
        "RULES_FILE_KEY": "rules-key",
        "VCITE_BUCKET": "vcite-tna-files",
        "VCITE_ENRICHED_BUCKET": "staging-vcite-enriched-bucket",
    }
    mock_validate_env.side_effect = lambda key: env_values[key]

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=env_values["RULES_FILE_BUCKET"])
    patterns = '{"pattern": "value"}\n{"pattern2": "value2"}'
    s3.put_object(Bucket=env_values["RULES_FILE_BUCKET"], Key=env_values["RULES_FILE_KEY"], Body=patterns)

    sqs_message = json.dumps(
        {
            "status": "ready",
            "uri_reference": "ewhc/ch/2023/257",
        },
    )

    event = {
        "Records": [
            _sqs_record("{}", event_value="s3:TestEvent"),
            _sqs_record(json.dumps({"Message": sqs_message})),
        ],
    }

    index.handler(event, None)

    assert mock_process_sqs.call_count == 1
    _, called_endpoint, called_user, called_password, called_pattern_list, called_vcite_enabled, called_vcite_bucket = (
        mock_process_sqs.call_args.args
    )
    assert called_endpoint == "https://api.staging.caselaw.nationalarchives.gov.uk/"
    assert called_user == "api-user"
    assert called_password == env_values["API_PASSWORD"]
    assert called_pattern_list == [
        {"pattern": "value"},
        {"pattern2": "value2"},
    ]
    assert called_vcite_enabled is False
    assert called_vcite_bucket == "vcite-tna-files"


@mock_aws
@patch("lambdas.enrichment_lambda.index._read_vcite_toggle", return_value="off")
@patch("lambdas.enrichment_lambda.index.patch_judgment")
@patch("lambdas.enrichment_lambda.index.enrich_xml_file", return_value="<enriched-body/>")
@patch("lambdas.enrichment_lambda.index.lock_judgment")
@patch("lambdas.enrichment_lambda.index.fetch_judgment", return_value="<source-xml/>")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_vcite_off_patches_directly(
    mock_validate_env,
    mock_fetch,
    mock_lock,
    mock_enrich,
    mock_patch,
    _mock_vcite_toggle,
):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "production",
        "RULES_FILE_BUCKET": "rules-bucket",
        "RULES_FILE_KEY": "rules-key",
        "VCITE_BUCKET": "vcite-tna-files",
        "VCITE_ENRICHED_BUCKET": "production-vcite-enriched-bucket",
    }
    mock_validate_env.side_effect = lambda key: env_values[key]

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=env_values["RULES_FILE_BUCKET"])
    patterns = '{"pattern": "value"}\n{"pattern2": "value2"}'
    s3.put_object(Bucket=env_values["RULES_FILE_BUCKET"], Key=env_values["RULES_FILE_KEY"], Body=patterns)

    sqs_message = {
        "Message": json.dumps(
            {
                "status": "ready",
                "uri_reference": "ewhc/ch/2023/257",
            },
        ),
    }

    event = {
        "Records": [
            _sqs_record(json.dumps(sqs_message)),
        ],
    }

    index.handler(event, None)

    mock_fetch.assert_called_once_with(
        "https://api.caselaw.nationalarchives.gov.uk/",
        "ewhc/ch/2023/257",
        "api-user",
        env_values["API_PASSWORD"],
    )
    mock_lock.assert_called_once_with(
        "https://api.caselaw.nationalarchives.gov.uk/",
        "ewhc/ch/2023/257",
        "api-user",
        env_values["API_PASSWORD"],
    )
    mock_enrich.assert_called_once_with(
        "<source-xml/>",
        [
            {"pattern": "value"},
            {"pattern2": "value2"},
        ],
        enrichment_version="7.4.0",
    )
    mock_patch.assert_called_once_with(
        "https://api.caselaw.nationalarchives.gov.uk/",
        "ewhc/ch/2023/257",
        "<enriched-body/>",
        "api-user",
        env_values["API_PASSWORD"],
    )


@mock_aws
@patch("lambdas.enrichment_lambda.index._read_vcite_toggle", return_value="on")
@patch("lambdas.enrichment_lambda.index._upload_to_vcite_bucket")
@patch("lambdas.enrichment_lambda.index.patch_judgment")
@patch("lambdas.enrichment_lambda.index.enrich_xml_file", return_value="<enriched-body/>")
@patch("lambdas.enrichment_lambda.index.lock_judgment")
@patch("lambdas.enrichment_lambda.index.fetch_judgment", return_value="<source-xml/>")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_vcite_on_uploads_and_skips_patch(
    mock_validate_env,
    mock_fetch,
    mock_lock,
    mock_enrich,
    mock_patch,
    mock_upload,
    _mock_vcite_toggle,
):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "production",
        "RULES_FILE_BUCKET": "rules-bucket",
        "RULES_FILE_KEY": "rules-key",
        "VCITE_BUCKET": "vcite-tna-files",
        "VCITE_ENRICHED_BUCKET": "production-vcite-enriched-bucket",
    }
    mock_validate_env.side_effect = lambda key: env_values[key]

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=env_values["RULES_FILE_BUCKET"])
    patterns = '{"pattern": "value"}\n{"pattern2": "value2"}'
    s3.put_object(Bucket=env_values["RULES_FILE_BUCKET"], Key=env_values["RULES_FILE_KEY"], Body=patterns)

    sqs_message = {
        "Message": json.dumps(
            {
                "status": "ready",
                "uri_reference": "ewhc/ch/2023/257",
            },
        ),
    }

    event = {
        "Records": [
            _sqs_record(json.dumps(sqs_message)),
        ],
    }

    index.handler(event, None)

    mock_fetch.assert_called_once()
    mock_lock.assert_called_once()
    mock_enrich.assert_called_once()
    mock_upload.assert_called_once_with("vcite-tna-files", "ewhc/ch/2023/257.xml", "<enriched-body/>")
    mock_patch.assert_not_called()


@mock_aws
@patch("lambdas.enrichment_lambda.index._read_vcite_toggle", return_value="off")
@patch("lambdas.enrichment_lambda.index.patch_judgment")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_vcite_callback_patches_returned_xml(
    mock_validate_env,
    mock_patch,
    _mock_vcite_toggle,
):
    bucket_name = "production-tna-s3-tna-sg-vcite-enriched-bucket"
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "production",
        "RULES_FILE_BUCKET": "rules-bucket",
        "RULES_FILE_KEY": "rules-key",
        "VCITE_BUCKET": "vcite-tna-files",
        "VCITE_ENRICHED_BUCKET": bucket_name,
    }
    mock_validate_env.side_effect = lambda key: env_values[key]

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)
    xml_key = "ewhc/ch/2023/257.xml"
    xml_body = "<akomaNtoso><judgment><p>vcite</p></judgment></akomaNtoso>"
    s3.put_object(Bucket=bucket_name, Key=xml_key, Body=xml_body.encode("utf-8"))

    event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "awsRegion": "eu-west-2",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": bucket_name},
                    "object": {"key": xml_key},
                },
            },
        ],
    }

    index.handler(event, None)

    called_endpoint, called_doc_uri, called_xml, called_user, called_password = mock_patch.call_args.args
    assert called_endpoint == "https://api.caselaw.nationalarchives.gov.uk/"
    assert called_doc_uri == "ewhc/ch/2023/257"
    assert "<akomaNtoso" in called_xml
    assert called_user == "api-user"
    assert called_password == env_values["API_PASSWORD"]
