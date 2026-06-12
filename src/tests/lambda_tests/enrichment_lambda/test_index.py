import json
from unittest.mock import Mock, patch

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
@patch("lambdas.enrichment_lambda.index.parse_file", return_value="parsed text")
@patch("lambdas.enrichment_lambda.index.lock_judgment")
@patch("lambdas.enrichment_lambda.index.fetch_judgment", return_value="<xml/>")
@patch("lambdas.enrichment_lambda.index.read_message", return_value=("ready", "uksc/2024/1"))
def test_process_event_happy_path(
    mock_read_message,
    mock_fetch,
    mock_lock,
    mock_parse,
    mock_enrich,
    mock_patch,
):
    sqs_record = Mock()
    sqs_record.body = json.dumps({"Message": "{}"})

    endpoint = APIEndpointBaseURL("https://api.example/")

    index.process_event(
        sqs_record,
        endpoint,
        "user",
        "pass",
    )

    mock_read_message.assert_called_once()
    mock_fetch.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")
    mock_lock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")
    mock_parse.assert_called_once_with("<xml/>")
    mock_enrich.assert_called_once_with("parsed text")
    mock_patch.assert_called_once_with(endpoint, "uksc/2024/1", "<enriched/>", "user", "pass")


@patch("lambdas.enrichment_lambda.index.process_event")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_uses_staging_endpoint_and_skips_s3_test_event(mock_validate_env, mock_process_event):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "staging",
    }
    mock_validate_env.side_effect = lambda key: env_values[key]

    event = {
        "Records": [
            _sqs_record("{}", event_value="s3:TestEvent"),
            _sqs_record(json.dumps({"Message": "{}"})),
        ],
    }

    index.handler(event, None)

    assert mock_process_event.call_count == 1
    called_record, called_endpoint, called_user, called_password = mock_process_event.call_args.args
    assert called_record.body == json.dumps({"Message": "{}"})
    assert called_endpoint == "https://api.staging.caselaw.nationalarchives.gov.uk/"
    assert called_user == "api-user"
    assert called_password == env_values["API_PASSWORD"]


@patch("lambdas.enrichment_lambda.index.patch_judgment")
@patch("lambdas.enrichment_lambda.index.enrich_xml_file", return_value="<enriched-body/>")
@patch("lambdas.enrichment_lambda.index.parse_file", return_value="plain text")
@patch("lambdas.enrichment_lambda.index.lock_judgment")
@patch("lambdas.enrichment_lambda.index.fetch_judgment", return_value="<source-xml/>")
@patch("lambdas.enrichment_lambda.index.validate_env_variable")
def test_handler_e2e_style_single_record(
    mock_validate_env,
    mock_fetch,
    mock_lock,
    mock_parse,
    mock_enrich,
    mock_patch,
):
    env_values = {
        "API_USERNAME": "api-user",
        "API_PASSWORD": "api-credential",
        "ENVIRONMENT": "production",
    }
    mock_validate_env.side_effect = lambda key: env_values[key]

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
    mock_parse.assert_called_once_with("<source-xml/>")
    mock_enrich.assert_called_once_with("plain text")
    mock_patch.assert_called_once_with(
        "https://api.caselaw.nationalarchives.gov.uk/",
        "ewhc/ch/2023/257",
        "<enriched-body/>",
        "api-user",
        env_values["API_PASSWORD"],
    )
