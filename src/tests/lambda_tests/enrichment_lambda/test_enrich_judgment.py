from unittest.mock import patch

import pytest

from lambdas.enrichment_lambda.enrich_judgment import enrich_judgment
from utils.custom_types import APIEndpointBaseURL


class TestEnrichJudgment:
    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_happy_path(
        self,
        mock_fetch,
        mock_lock,
        mock_enrich,
        mock_patch,
        mock_unlock,
    ):
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        enrich_judgment(
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
        mock_unlock.assert_not_called()

    @patch("boto3.resource")
    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_vcite_enabled(
        self,
        mock_fetch,
        mock_lock,
        mock_enrich,
        mock_patch,
        mock_unlock,
        mock_s3_resource,
    ):
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")
        mock_s3_object = mock_s3_resource.return_value.Object.return_value

        enrich_judgment(
            uri_reference,
            endpoint,
            "user",
            "pass",
            pattern_list=[{"pattern": "value"}],
            vcite_enabled=True,
            vcite_bucket="vcite-bucket",
        )

        mock_fetch.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")
        mock_lock.assert_called_once()
        mock_enrich.assert_called_once()
        mock_s3_resource.return_value.Object.assert_called_once_with("vcite-bucket", "uksc/2024/1.xml")
        mock_s3_object.put.assert_called_once()
        mock_patch.assert_not_called()
        mock_unlock.assert_not_called()

    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment")
    def test_enrich_judgment_fetch_failure(self, mock_fetch, mock_lock, mock_enrich, mock_patch, mock_unlock):
        mock_fetch.side_effect = Exception("API error")
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="API error"):
            enrich_judgment(uri_reference, endpoint, "user", "pass", [])

        mock_lock.assert_called()
        mock_enrich.assert_not_called()
        mock_patch.assert_not_called()
        mock_unlock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")

    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_patch_failure(self, mock_fetch, mock_lock, mock_enrich, mock_patch, mock_unlock):
        mock_patch.side_effect = Exception("Patch failed")
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="Patch failed"):
            enrich_judgment(uri_reference, endpoint, "user", "pass", [])

        mock_fetch.assert_called_once()
        mock_lock.assert_called_once()
        mock_enrich.assert_called_once()
        mock_patch.assert_called_once_with(endpoint, "uksc/2024/1", "<enriched/>", "user", "pass")
        mock_unlock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")

    @patch("boto3.resource")
    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_vcite_upload_failure(
        self,
        mock_fetch,
        mock_lock,
        mock_enrich,
        mock_patch,
        mock_unlock,
        mock_s3_resource,
    ):
        mock_s3_object = mock_s3_resource.return_value.Object.return_value
        mock_s3_object.put.side_effect = Exception("vCite upload failed")
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="vCite upload failed"):
            enrich_judgment(
                uri_reference,
                endpoint,
                "user",
                "pass",
                [],
                vcite_enabled=True,
                vcite_bucket="vcite-bucket",
            )

        mock_patch.assert_not_called()
        mock_unlock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")

    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_lock_failure(self, mock_fetch, mock_lock, mock_enrich, mock_patch, mock_unlock):
        mock_lock.side_effect = Exception("Lock failed")
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="Lock failed"):
            enrich_judgment(uri_reference, endpoint, "user", "pass", [])

        mock_fetch.assert_not_called()
        mock_enrich.assert_not_called()
        mock_patch.assert_not_called()
        mock_unlock.assert_not_called()

    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_enrich_failure(self, mock_fetch, mock_lock, mock_enrich, mock_patch, mock_unlock):
        mock_enrich.side_effect = Exception("Enrichment pipeline failed")
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="Enrichment pipeline failed"):
            enrich_judgment(uri_reference, endpoint, "user", "pass", [])

        mock_fetch.assert_called_once()
        mock_lock.assert_called_once()
        mock_patch.assert_not_called()
        mock_unlock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")

    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_unlock_failure_does_not_mask_original_error(
        self,
        mock_fetch,
        mock_lock,
        mock_enrich,
        mock_patch,
        mock_unlock,
    ):
        mock_enrich.side_effect = Exception("Enrichment pipeline failed")
        mock_unlock.side_effect = RuntimeError("Unlock failed")
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        with pytest.raises(Exception, match="Enrichment pipeline failed"):
            enrich_judgment(uri_reference, endpoint, "user", "pass", [])

        mock_fetch.assert_called_once()
        mock_lock.assert_called_once()
        mock_patch.assert_not_called()
        mock_unlock.assert_called_once_with(endpoint, "uksc/2024/1", "user", "pass")

    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_with_empty_pattern_list(self, mock_fetch, mock_lock, mock_enrich, mock_patch, mock_unlock):
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")

        enrich_judgment(
            uri_reference,
            endpoint,
            "user",
            "pass",
            pattern_list=[],
        )

        mock_fetch.assert_called_once()
        mock_lock.assert_called_once()
        mock_enrich.assert_called_once_with("<xml/>", [], enrichment_version="7.4.0")
        mock_patch.assert_called_once()
        mock_unlock.assert_not_called()

    @patch("boto3.resource")
    @patch("lambdas.enrichment_lambda.enrich_judgment.unlock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.patch_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.enrich_xml", return_value="<enriched/>")
    @patch("lambdas.enrichment_lambda.enrich_judgment.lock_judgment")
    @patch("lambdas.enrichment_lambda.enrich_judgment.fetch_judgment", return_value="<xml/>")
    def test_enrich_judgment_vcite_enabled_with_empty_bucket_name(
        self,
        mock_fetch,
        mock_lock,
        mock_enrich,
        mock_patch,
        mock_unlock,
        mock_s3_resource,
    ):
        uri_reference = "uksc/2024/1"
        endpoint = APIEndpointBaseURL("https://api.example/")
        mock_s3_object = mock_s3_resource.return_value.Object.return_value

        enrich_judgment(
            uri_reference,
            endpoint,
            "user",
            "pass",
            [],
            vcite_enabled=True,
            vcite_bucket="",
        )

        mock_s3_resource.return_value.Object.assert_called_once_with("", "uksc/2024/1.xml")
        mock_s3_object.put.assert_called_once()
        mock_patch.assert_not_called()
        mock_unlock.assert_not_called()
