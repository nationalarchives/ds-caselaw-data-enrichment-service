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
def test_process_event_happy_path(
    mock_fetch,
    mock_lock,
    mock_enrich,
    mock_patch,
):
    uri_reference = "uksc/2024/1"
    endpoint = APIEndpointBaseURL("https://api.example/")

    index.process_event(
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
@patch("lambdas.enrichment_lambda.index.process_event")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_uses_staging_endpoint_and_skips_s3_test_event(mock_validate_env, mock_process_event):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "staging",
        "RULES_FILE_BUCKET": "rules-bucket",
        "RULES_FILE_KEY": "rules-key",
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
    assert mock_process_event.call_count == 1
    called_uri_reference, called_endpoint, called_user, called_password, called_pattern_list = (
        mock_process_event.call_args.args
    )
    assert called_uri_reference == "ewhc/ch/2023/257"
    assert called_endpoint == "https://api.staging.caselaw.nationalarchives.gov.uk/"
    assert called_user == "api-user"
    assert called_password == env_values["API_PASSWORD"]
    assert called_pattern_list == [
        {"pattern": "value"},
        {"pattern2": "value2"},
    ]


@mock_aws
@patch("lambdas.enrichment_lambda.index.patch_judgment")
@patch("lambdas.enrichment_lambda.index.enrich_xml_file", return_value="<enriched-body/>")
@patch("lambdas.enrichment_lambda.index.lock_judgment")
@patch("lambdas.enrichment_lambda.index.fetch_judgment", return_value="<source-xml/>")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_e2e_style_single_record(
    mock_validate_env,
    mock_fetch,
    mock_lock,
    mock_enrich,
    mock_patch,
):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "production",
        "RULES_FILE_BUCKET": "rules-bucket",
        "RULES_FILE_KEY": "rules-key",
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
