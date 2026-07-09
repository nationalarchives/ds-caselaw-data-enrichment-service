import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import boto3
import lxml.etree
import pytest
from caselawclient.Client import DEFAULT_USER_AGENT, MarklogicApiClient
from caselawclient.models.documents import DocumentURIString
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.judgments import Judgment
from dotenv import load_dotenv

from lambdas.enrichment_lambda.api import (
    fetch_judgment,
    lock_judgment,
    patch_judgment,
)
from lambdas.enrichment_lambda.index import handler
from utils.custom_types import APIEndpointBaseURL

LOGGER = logging.getLogger(__name__)


# Load project root .env first, then E2E-specific overrides if present.
# Assuming this file's path is: <repo>/src/tests/end_to_end_tests/test_marklogic_e2e.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.e2e", override=True)


@dataclass(frozen=True)
class E2EConfig:
    aws_region: str
    api_endpoint: APIEndpointBaseURL
    api_username: str
    api_password: str
    uri: str
    rules_bucket: str
    api_secret_name: str | None
    rules_key: str
    vcite_bucket: str
    vcite_enriched_bucket: str
    trigger_mode: str
    timeout_seconds: int
    seed_if_missing: bool
    should_restore: bool
    sqs_queue_name: str | None
    source_xml_path: str | None
    marklogic_api_client_host: str | None
    marklogic_use_https: bool | None
    marklogic_secret_name: str | None
    marklogic_username: str | None
    marklogic_password: str | None
    database_name: str | None
    database_username: str | None
    db_password_secret_name: str | None
    e2e_db_host: str | None
    e2e_db_port: str | None

    @classmethod
    def from_env(cls) -> "E2EConfig":
        aws_region = _require_any_env("AWS_REGION", "AWS_DEFAULT_REGION")
        uri = _require_env("E2E_URI")
        trigger_mode = os.getenv("E2E_TRIGGER_MODE", "sqs").lower()
        if trigger_mode not in {"sqs", "local_handler"}:
            pytest.fail("Invalid E2E_TRIGGER_MODE. Use 'sqs' or 'local_handler'.")

        seed_if_missing = os.getenv("E2E_SEED_IF_MISSING", "false") == "true"

        sqs_queue_name = _require_env("SQS_ENRICHMENT_QUEUE_NAME") if trigger_mode == "sqs" else None

        if seed_if_missing:
            marklogic_api_client_host = _require_env("MARKLOGIC_API_CLIENT_HOST")
            if "://" in marklogic_api_client_host:
                pytest.fail("MARKLOGIC_API_CLIENT_HOST must be host[:port] without scheme")
            marklogic_use_https = _require_env("MARKLOGIC_USE_HTTPS").strip().lower() == "true"
        else:
            marklogic_api_client_host = os.getenv("MARKLOGIC_API_CLIENT_HOST")
            marklogic_use_https = (
                os.getenv("MARKLOGIC_USE_HTTPS", "false").strip().lower() == "true"
                if os.getenv("MARKLOGIC_USE_HTTPS") is not None
                else None
            )

        marklogic_secret_name = os.getenv("MARKLOGIC_SECRET_NAME")
        marklogic_username = os.getenv("MARKLOGIC_USERNAME")
        marklogic_password = os.getenv("MARKLOGIC_PASSWORD")
        if (marklogic_username and not marklogic_password) or (marklogic_password and not marklogic_username):
            pytest.fail(
                "Both MARKLOGIC_USERNAME and MARKLOGIC_PASSWORD must be set when using explicit credentials",
            )

        api_username = _require_env("API_USERNAME")
        api_password = _require_env("API_PASSWORD")
        api_secret_name = os.getenv("API_SECRET_NAME")  # Optional, only used for local_handler

        if trigger_mode == "local_handler":
            database_name = _require_env("DATABASE_NAME")
            database_username = _require_env("DATABASE_USERNAME")
            db_password_secret_name = _require_env("DB_PASSWORD_SECRET_NAME")
            e2e_db_host = _require_env("E2E_DB_HOST")
            e2e_db_port = _require_env("E2E_DB_PORT")
        else:
            database_name = None
            database_username = None
            db_password_secret_name = None
            e2e_db_host = None
            e2e_db_port = None

        return cls(
            aws_region=aws_region,
            api_endpoint=APIEndpointBaseURL(_require_env("API_ENDPOINT")),
            uri=uri,
            rules_bucket=_require_env("RULES_FILE_BUCKET"),
            rules_key=_require_env("RULES_FILE_KEY"),
            vcite_bucket=_require_env("VCITE_BUCKET"),
            vcite_enriched_bucket=_require_env("VCITE_ENRICHED_BUCKET"),
            trigger_mode=trigger_mode,
            timeout_seconds=int(os.getenv("E2E_TIMEOUT_SECONDS", "180")),
            seed_if_missing=seed_if_missing,
            should_restore=os.getenv("E2E_RESTORE_ORIGINAL", "true") == "true",
            sqs_queue_name=sqs_queue_name,
            source_xml_path=os.getenv("E2E_SOURCE_XML_PATH"),
            marklogic_api_client_host=marklogic_api_client_host,
            marklogic_use_https=marklogic_use_https,
            marklogic_secret_name=marklogic_secret_name,
            marklogic_username=marklogic_username,
            marklogic_password=marklogic_password,
            api_username=api_username,
            api_password=api_password,
            database_name=database_name,
            database_username=database_username,
            db_password_secret_name=db_password_secret_name,
            e2e_db_host=e2e_db_host,
            e2e_db_port=e2e_db_port,
            api_secret_name=api_secret_name,
        )


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.fail(f"Missing required env var for E2E: {name}")
    return value


def _require_any_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    pytest.fail(f"Missing required env var for E2E: one of {', '.join(names)}")


def _create_marklogic_client_for_fixture(cfg: E2EConfig) -> MarklogicApiClient:
    if not cfg.marklogic_api_client_host or cfg.marklogic_use_https is None:
        pytest.fail(
            "Fixture seeding requires MARKLOGIC_API_CLIENT_HOST and MARKLOGIC_USE_HTTPS",
        )

    return MarklogicApiClient(
        host=cfg.marklogic_api_client_host,
        username=cfg.api_username,
        password=cfg.api_password,
        use_https=cfg.marklogic_use_https,
        user_agent=f"ds-caselaw-data-enrichment-service/e2e {DEFAULT_USER_AGENT}",
    )


def _seed_fixture_document_from_repo_xml(cfg: E2EConfig, target_uri: str) -> bool:
    source_xml_path = cfg.source_xml_path
    if not source_xml_path:
        return False

    xml_path = Path(source_xml_path)
    if not xml_path.is_absolute():
        xml_path = PROJECT_ROOT / xml_path

    if not xml_path.exists():
        pytest.fail(f"Fixture XML path does not exist: {xml_path}")

    marklogic_client = _create_marklogic_client_for_fixture(cfg)
    target = DocumentURIString(target_uri)

    if marklogic_client.document_exists(target):
        return False

    xml_element = lxml.etree.fromstring(xml_path.read_bytes())
    annotation = VersionAnnotation(
        version_type=VersionType.SUBMISSION,
        automated=True,
        message="e2e fixture seed",
    )
    marklogic_client.insert_document_xml(target, xml_element, Judgment, annotation)

    # Set published property to false so Priv API can fetch unpublished docs
    marklogic_client.set_property(target, "published", "false")

    return True


def _delete_fixture_document_if_created(
    cfg: E2EConfig,
    target_uri: str,
    fixture_was_created: bool,
) -> None:
    if not fixture_was_created:
        return
    marklogic_client = _create_marklogic_client_for_fixture(cfg)
    marklogic_client.delete_judgment(DocumentURIString(target_uri))


def _get_queue_url(cfg: E2EConfig) -> str:
    if not cfg.sqs_queue_name:
        pytest.fail("SQS_ENRICHMENT_QUEUE_NAME is required for sqs trigger mode")
    sqs = boto3.client("sqs", region_name=cfg.aws_region)
    response = sqs.get_queue_url(QueueName=cfg.sqs_queue_name)
    return response["QueueUrl"]


def _send_enrichment_message(aws_region: str, queue_url: str, uri_reference: str) -> None:
    sqs = boto3.client("sqs", region_name=aws_region)
    message_payload = {
        "Message": json.dumps(
            {
                "status": "ready",
                "uri_reference": uri_reference,
            },
        ),
    }
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_payload),
    )


def _build_sqs_event(uri_reference: str, aws_region: str) -> dict:
    return {
        "Records": [
            {
                "messageId": "e2e-1",
                "receiptHandle": "e2e-rh",
                "body": json.dumps(
                    {
                        "Message": json.dumps(
                            {
                                "status": "ready",
                                "uri_reference": uri_reference,
                            },
                        ),
                    },
                ),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "0",
                    "SenderId": "e2e",
                    "ApproximateFirstReceiveTimestamp": "0",
                },
                "messageAttributes": {},
                "md5OfBody": "x",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:eu-west-2:123456789012:e2e",
                "awsRegion": aws_region,
            },
        ],
    }


def _configure_local_handler_db_env(monkeypatch, cfg: E2EConfig) -> None:
    """Configure DB env vars for local handler execution mode.

    Set E2E_DB_HOST/E2E_DB_PORT explicitly
    (for example 127.0.0.1:15432).
    """
    if not all(
        [
            cfg.database_name,
            cfg.database_username,
            cfg.db_password_secret_name,
            cfg.e2e_db_host,
            cfg.e2e_db_port,
        ],
    ):
        pytest.fail(
            "local_handler mode requires DATABASE_NAME, DATABASE_USERNAME, DB_PASSWORD_SECRET_NAME, "
            "E2E_DB_HOST, and E2E_DB_PORT",
        )

    monkeypatch.setenv("DATABASE_NAME", cfg.database_name)
    monkeypatch.setenv("DATABASE_USERNAME", cfg.database_username)
    monkeypatch.setenv("DB_PASSWORD_SECRET_NAME", cfg.db_password_secret_name)
    monkeypatch.setenv("DATABASE_HOSTNAME", cfg.e2e_db_host)
    monkeypatch.setenv("DATABASE_PORT", cfg.e2e_db_port)


def _configure_enrichment_handler_env(monkeypatch, cfg: E2EConfig) -> None:
    monkeypatch.setenv("API_ENDPOINT", str(cfg.api_endpoint))
    monkeypatch.setenv("VCITE_ENABLED", "false")
    monkeypatch.setenv("VCITE_BUCKET", cfg.vcite_bucket)
    monkeypatch.setenv("VCITE_ENRICHED_BUCKET", cfg.vcite_enriched_bucket)
    monkeypatch.setenv("RULES_FILE_BUCKET", cfg.rules_bucket)
    monkeypatch.setenv("RULES_FILE_KEY", cfg.rules_key)
    monkeypatch.setenv("AWS_DEFAULT_REGION", cfg.aws_region)
    # API_SECRET_NAME required only for local_handler mode (Lambda needs SM access)
    if cfg.trigger_mode == "local_handler" and cfg.api_secret_name:
        monkeypatch.setenv("API_SECRET_NAME", cfg.api_secret_name)


def _latest_tna_enriched_date(xml: str) -> str | None:
    dates = re.findall(r'<FRBRdate date="([^"]+)" name="tna-enriched"', xml)
    return max(dates) if dates else None


def _wait_for_enrichment(
    api_endpoint: APIEndpointBaseURL,
    uri: str,
    username: str,
    password: str,
    before_xml: str,
    timeout_seconds: int = 180,
) -> str:
    before_latest_enriched_date = _latest_tna_enriched_date(before_xml)

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        current_xml = fetch_judgment(api_endpoint, uri, username, password)
        current_latest_enriched_date = _latest_tna_enriched_date(current_xml)

        # Existing URIs can already have one enrichment tag; detect a fresh run by timestamp change.
        if current_latest_enriched_date and current_latest_enriched_date != before_latest_enriched_date:
            return current_xml

        # Fallback for docs where timestamp extraction is unavailable.
        if current_xml != before_xml and "<uk:tna-enrichment-engine" in current_xml:
            return current_xml
        time.sleep(5)

    pytest.fail(
        f"Timed out waiting for enrichment result for {uri}. "
        "Expected tna-enriched timestamp (or document XML) to change.",
    )


def _wait_for_judgment_fetchable(
    api_endpoint: APIEndpointBaseURL,
    uri: str,
    username: str,
    password: str,
    timeout_seconds: int = 60,
) -> None:
    """Wait briefly for Priv API lookup to observe a newly seeded fixture."""
    last_error: RuntimeError | None = None
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            fetch_judgment(api_endpoint, uri, username, password)
            return
        except RuntimeError as exc:
            last_error = exc
            time.sleep(3)
    pytest.fail(
        f"Timed out waiting for Priv API to fetch seeded document at judgment/{uri}. Last Priv API error: {last_error}",
    )


def _trigger_enrichment(monkeypatch, cfg: E2EConfig) -> None:
    if cfg.trigger_mode == "sqs":
        queue_url = _get_queue_url(cfg)
        _send_enrichment_message(cfg.aws_region, queue_url, cfg.uri)
        return

    if cfg.trigger_mode == "local_handler":
        _configure_local_handler_db_env(monkeypatch, cfg)
        handler(_build_sqs_event(cfg.uri, cfg.aws_region), None)
        return

    pytest.fail("Invalid E2E_TRIGGER_MODE. Use 'sqs' or 'local_handler'.")


@pytest.mark.e2e
def test_enrichment_lambda_triggers_and_updates_marklogic(monkeypatch):
    cfg = E2EConfig.from_env()
    _configure_enrichment_handler_env(monkeypatch, cfg)

    try:
        fixture_was_created = False
        if cfg.seed_if_missing:
            fixture_was_created = _seed_fixture_document_from_repo_xml(cfg, cfg.uri)

        if fixture_was_created:
            _wait_for_judgment_fetchable(cfg.api_endpoint, cfg.uri, cfg.api_username, cfg.api_password)

        before_xml = fetch_judgment(cfg.api_endpoint, cfg.uri, cfg.api_username, cfg.api_password)

        _trigger_enrichment(monkeypatch, cfg)

        after_xml = _wait_for_enrichment(
            cfg.api_endpoint,
            cfg.uri,
            cfg.api_username,
            cfg.api_password,
            before_xml,
            cfg.timeout_seconds,
        )
        assert "<akomaNtoso" in after_xml
        assert "<uk:tna-enrichment-engine" in after_xml
        assert after_xml != before_xml
    finally:
        if fixture_was_created:
            _delete_fixture_document_if_created(cfg, cfg.uri, fixture_was_created)
        elif cfg.should_restore:
            try:
                lock_judgment(cfg.api_endpoint, cfg.uri, cfg.api_username, cfg.api_password)
                patch_judgment(cfg.api_endpoint, cfg.uri, before_xml, cfg.api_username, cfg.api_password)
            except RuntimeError as exc:
                # Do not mask enrichment result with restore races on shared docs.
                if "content hash" in str(exc).lower():
                    LOGGER.warning(
                        "Skipping restore for %s due to content hash mismatch in shared environment: %s",
                        cfg.uri,
                        exc,
                    )
                else:
                    raise
