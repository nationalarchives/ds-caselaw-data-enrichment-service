from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws
from requests.auth import HTTPBasicAuth

from lambdas.push_enriched_xml.index import (  # noqa: E402
    process_event,
)


@pytest.mark.parametrize(
    "source_key_prefix",
    ["uksc/2024/1", "d-d911a2bd-72ef-44ab-8bbb-dfd1b632dded/press-summary/1"],
)
@mock_aws
@patch("lambdas.push_enriched_xml.index.requests")
def test_push_enriched_xml(requests_mock, monkeypatch, source_key_prefix):
    """
    Given a SQS record for a XML file in S3 with .xml suffix,
    When process_event function is called with it
    Then it fetches XML content from S3, and sends a PATCH request to the API endpoint
    for the URI corresponding to the XML file, with the canonicalized version of the XML as the body.
    """

    # Setup mock S3
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="test_bucket")

    # Non-canonical XML: redundant xmlns on child
    non_canonical_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <root xmlns="urn:foo" xmlns:bar="urn:bar" attr2="2" attr1="1">
        <parent attr="p1" xmlns:bar="urn:bar">
            <child1 bar:attr="b1" attr="c1" xmlns="urn:foo" xmlns:bar="urn:bar">
                <subchild attr="s1" bar:attr="sb1">
                    value
                </subchild>
            </child1>
            <child2 attr="c2" xmlns="urn:foo">
                <subchild2 attr="s2"/>
            </child2>
        </parent>
        <emptychild xmlns="urn:foo" />
    </root>
    """
    s3.put_object(Bucket="test_bucket", Key=f"{source_key_prefix}.xml", Body=non_canonical_xml)

    class FakeSQSRecord(dict):
        def __init__(self):
            self.body = '{"Validated": true}'
            self["messageAttributes"] = {
                "source_key": {"stringValue": f"{source_key_prefix}.xml"},
                "source_bucket": {"stringValue": "test_bucket"},
            }

    process_event(FakeSQSRecord())

    # Assert that the requests.patch method was called with the correct data
    requests_mock.patch.assert_called_once()
    args, kwargs = requests_mock.patch.call_args
    expected_canonical = b"""<root xmlns="urn:foo" xmlns:bar="urn:bar" attr1="1" attr2="2">
        <parent attr="p1">
            <child1 attr="c1" bar:attr="b1">
                <subchild attr="s1" bar:attr="sb1">
                    value
                </subchild>
            </child1>
            <child2 attr="c2">
                <subchild2 attr="s2"></subchild2>
            </child2>
        </parent>
        <emptychild></emptychild>
    </root>"""

    assert kwargs["data"] == expected_canonical
    assert kwargs["params"] == {"unlock": True}
    assert isinstance(kwargs["auth"], HTTPBasicAuth)
    assert (
        kwargs["auth"].username == "TEST_USERNAME"
    )  # come from pytest.ini, should change this but will break other tests, without setting env vars for each, so will leave for now
    assert kwargs["auth"].password == "TEST_PASSWORD"  # noqa: S105
    assert kwargs["timeout"] == 10
    assert args[0] == f"https://api.caselaw.nationalarchives.gov.uk/judgment/{source_key_prefix}"
