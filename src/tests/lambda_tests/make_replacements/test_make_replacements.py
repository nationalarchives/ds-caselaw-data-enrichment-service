import json

import boto3
from moto import mock_aws

from lambdas.make_replacements.index import process_event


class FakeSQSRecord(dict):
    def __init__(self, body, message_attributes):
        self.body = json.dumps(body)
        self["messageAttributes"] = message_attributes


@mock_aws
def test_process_event_basic():
    # Set up mock AWS resources
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="test_bucket")

    # Create test input XML
    input_xml = """<akomaNtoso>
        <judgment>
            <header>Some header content</header>
            <judgmentBody>
                <p>Test content before</p>
                <origin-ref>Content to replace</origin-ref>
                <p>Test content after</p>
            </judgmentBody>
        </judgment>
    </akomaNtoso>"""

    # Upload test file to mock S3
    s3.put_object(
        Bucket="test_bucket",
        Key="test.xml",
        Body=input_xml,
    )

    # Create mock SQS event
    sqs_record = FakeSQSRecord(
        body={"Validated": True},
        message_attributes={
            "source_bucket": {"stringValue": "test_bucket"},
            "source_key": {"stringValue": "test.xml"},
        },
    )

    # Call the function
    process_event(sqs_record)

    # Get the processed file from S3
    response = s3.get_object(Bucket="test_bucket", Key="test.xml")
    processed_content = response["Body"].read().decode()

    # Verify replacements
    assert "<origin-ref>" not in processed_content
    assert "Content to replace" in processed_content
    assert "<p>Test content before</p>" in processed_content
    assert "<p>Test content after</p>" in processed_content


@mock_aws
def test_process_event_multiple_replacements():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="test_bucket")

    input_xml = """<akomaNtoso>
        <judgment>
            <header>Some header content</header>
            <judgmentBody>
                <origin-ref>First replacement</origin-ref>
                <p>Middle content</p>
                <origin-ref>Second replacement</origin-ref>
            </judgmentBody>
        </judgment>
    </akomaNtoso>"""

    s3.put_object(
        Bucket="test_bucket",
        Key="test.xml",
        Body=input_xml,
    )

    sqs_record = FakeSQSRecord(
        body={"Validated": True},
        message_attributes={
            "source_bucket": {"stringValue": "test_bucket"},
            "source_key": {"stringValue": "test.xml"},
        },
    )

    process_event(sqs_record)

    response = s3.get_object(Bucket="test_bucket", Key="test.xml")
    processed_content = response["Body"].read().decode()

    assert "<origin-ref>" not in processed_content
    assert "First replacement" in processed_content
    assert "Second replacement" in processed_content
    assert "<p>Middle content</p>" in processed_content


@mock_aws
def test_process_event_no_replacements_needed():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="test_bucket")

    input_xml = """<akomaNtoso>
        <judgment>
            <header>Some header content</header>
            <judgmentBody>
                <p>Content with no replacements needed</p>
            </judgmentBody>
        </judgment>
    </akomaNtoso>"""

    s3.put_object(
        Bucket="test_bucket",
        Key="test.xml",
        Body=input_xml,
    )

    sqs_record = FakeSQSRecord(
        body={"Validated": True},
        message_attributes={
            "source_bucket": {"stringValue": "test_bucket"},
            "source_key": {"stringValue": "test.xml"},
        },
    )

    process_event(sqs_record)

    response = s3.get_object(Bucket="test_bucket", Key="test.xml")
    processed_content = response["Body"].read().decode()

    assert processed_content == input_xml
