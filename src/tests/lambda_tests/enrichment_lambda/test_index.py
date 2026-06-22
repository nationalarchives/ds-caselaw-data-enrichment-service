import json
from unittest.mock import patch

import boto3
from moto import mock_aws

from lambdas.enrichment_lambda import index


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


class TestHandler:
    @mock_aws
    @patch("lambdas.enrichment_lambda.index.enrich_judgment")
    @patch("lambdas.enrichment_lambda.index.validate_env_variable")
    def test_handler_uses_staging_endpoint_and_skips_s3_test_event(
        self,
        mock_validate_env,
        mock_enrich_judgment,
    ):
        env_values = {
            "API_USERNAME": "api-user",
            "API_PASSWORD": "api-credential",
            "ENVIRONMENT": "staging",
            "RULES_FILE_BUCKET": "rules-bucket",
            "RULES_FILE_KEY": "rules-key",
            "VCITE_BUCKET": "vcite-tna-files",
            "VCITE_ENRICHED_BUCKET": "staging-vcite-enriched-bucket",
            "VCITE_ENABLED": "false",
        }
        mock_validate_env.side_effect = lambda key: env_values[key]

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=env_values["RULES_FILE_BUCKET"])
        patterns = '{"pattern": "value"}\n{"pattern2": "value2"}'
        s3.put_object(
            Bucket=env_values["RULES_FILE_BUCKET"],
            Key=env_values["RULES_FILE_KEY"],
            Body=patterns,
        )

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

        # Should skip the TestEvent and call enrich_judgment for the valid record
        assert mock_enrich_judgment.call_count == 1
        call_args = mock_enrich_judgment.call_args
        assert call_args[0][0] == "ewhc/ch/2023/257"  # uri_reference
        assert call_args[0][1] == "https://api.staging.caselaw.nationalarchives.gov.uk/"  # endpoint
        assert call_args[0][2] == "api-user"  # api_username
        assert call_args[0][3] == env_values["API_PASSWORD"]  # api_password
        assert call_args[0][4] == [
            {"pattern": "value"},
            {"pattern2": "value2"},
        ]  # pattern_list
        assert call_args[0][5] is False  # vcite_enabled
        assert call_args[0][6] == "vcite-tna-files"  # vcite_bucket

    @mock_aws
    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.patch_judgment")
    @patch("lambdas.enrichment_lambda.index.validate_env_variable")
    def test_handler_vcite_callback_patches_returned_xml(
        self,
        mock_validate_env,
        mock_patch,
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
            "VCITE_ENABLED": "true",
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
