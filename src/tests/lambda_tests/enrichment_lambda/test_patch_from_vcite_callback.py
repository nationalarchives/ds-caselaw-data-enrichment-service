from unittest.mock import MagicMock, patch

import pytest

from lambdas.enrichment_lambda.patch_from_vcite_callback import patch_from_vcite_callback
from utils.custom_types import APIEndpointBaseURL


class TestPatchFromVciteCallback:
    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.patch_judgment")
    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.boto3.client")
    def test_patch_from_vcite_callback_success(self, mock_s3_client, mock_patch_judgment):
        mock_client = MagicMock()
        mock_s3_client.return_value = mock_client
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=b"<xml/>")),
        }

        record = {
            "s3": {
                "bucket": {"name": "vcite-bucket"},
                "object": {"key": "uksc/2024/1.xml"},
            },
        }
        api_endpoint = APIEndpointBaseURL("https://api.example/")

        patch_from_vcite_callback(record, api_endpoint, "user", "pass")

        mock_client.get_object.assert_called_once_with(Bucket="vcite-bucket", Key="uksc/2024/1.xml")
        mock_patch_judgment.assert_called_once()
        call_args = mock_patch_judgment.call_args
        assert call_args[0][0] == api_endpoint
        assert call_args[0][1] == "uksc/2024/1"
        assert call_args[0][3] == "user"
        assert call_args[0][4] == "pass"

    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.patch_judgment")
    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.boto3.client")
    def test_patch_from_vcite_callback_with_url_encoded_key(self, mock_s3_client, mock_patch_judgment):
        mock_client = MagicMock()
        mock_s3_client.return_value = mock_client
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=b"<xml/>")),
        }

        record = {
            "s3": {
                "bucket": {"name": "vcite-bucket"},
                "object": {"key": "uksc%2F2024%2F1.xml"},
            },
        }
        api_endpoint = APIEndpointBaseURL("https://api.example/")

        patch_from_vcite_callback(record, api_endpoint, "user", "pass")

        mock_client.get_object.assert_called_once_with(Bucket="vcite-bucket", Key="uksc/2024/1.xml")
        mock_patch_judgment.assert_called_once()
        call_args = mock_patch_judgment.call_args
        assert call_args[0][1] == "uksc/2024/1"

    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.patch_judgment")
    @patch("lambdas.enrichment_lambda.patch_from_vcite_callback.boto3.client")
    def test_patch_from_vcite_callback_s3_failure(self, mock_s3_client, mock_patch_judgment):
        mock_client = MagicMock()
        mock_s3_client.return_value = mock_client
        mock_client.get_object.side_effect = Exception("S3 error")

        record = {
            "s3": {
                "bucket": {"name": "vcite-bucket"},
                "object": {"key": "uksc/2024/1.xml"},
            },
        }
        api_endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="S3 error"):
            patch_from_vcite_callback(record, api_endpoint, "user", "pass")

        mock_patch_judgment.assert_not_called()
