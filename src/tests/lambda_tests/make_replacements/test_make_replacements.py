import boto3
from moto import mock_aws

from lambdas.make_replacements.index import process_event


@mock_aws
def test_process_event_basic():
    # Set up mock AWS resources
    s3 = boto3.client("s3")
    # Create all required buckets
    s3.create_bucket(Bucket="source-bucket")
    s3.create_bucket(Bucket="dest-bucket")
    s3.create_bucket(Bucket="replacements-bucket")

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

    # Upload XML to source bucket
    s3.put_object(
        Bucket="source-bucket",
        Key="test.xml",
        Body=input_xml,
    )

    # Add replacements file with an origin-ref replacement
    replacement_content = '{"ref": ["Content to replace", "", "", "", true]}'
    s3.put_object(
        Bucket="replacements-bucket",
        Key="test.xml",
        Body=replacement_content,
    )

    # Create mock SQS event
    sqs_record = {
        "messageAttributes": {
            "source_key": {"stringValue": "test.xml"},
            "source_bucket": {"stringValue": "source-bucket"},
        },
    }

    # Call the function with distinct buckets
    process_event(sqs_record, "dest-bucket", "source-bucket", "replacements-bucket")

    # Get the processed file from S3
    response = s3.get_object(Bucket="dest-bucket", Key="test.xml")
    processed_content = response["Body"].read().decode()

    # Verify the exact output XML
    expected_xml = """<akomaNtoso>
        <judgment>
            <header>Some header content</header>
            <judgmentBody>
                <p>Test content before</p>
                Content to replace
                <p>Test content after</p>
            </judgmentBody>
        </judgment>
    </akomaNtoso>"""
    assert processed_content == expected_xml


@mock_aws
def test_process_event_multiple_replacements():
    s3 = boto3.client("s3")
    # Create all required buckets
    s3.create_bucket(Bucket="source-bucket")
    s3.create_bucket(Bucket="dest-bucket")
    s3.create_bucket(Bucket="replacements-bucket")

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

    # Upload XML to source bucket
    s3.put_object(
        Bucket="source-bucket",
        Key="test.xml",
        Body=input_xml,
    )

    # Add replacements file with multiple replacements
    replacement_content = (
        '{"ref": ["First replacement", "", "", "", true]}\n{"ref": ["Second replacement", "", "", "", true]}'
    )
    s3.put_object(
        Bucket="replacements-bucket",
        Key="test.xml",
        Body=replacement_content,
    )

    sqs_record = {
        "messageAttributes": {
            "source_key": {"stringValue": "test.xml"},
            "source_bucket": {"stringValue": "source-bucket"},
        },
    }

    process_event(sqs_record, "dest-bucket", "source-bucket", "replacements-bucket")

    response = s3.get_object(Bucket="dest-bucket", Key="test.xml")
    processed_content = response["Body"].read().decode()

    expected_xml = """<akomaNtoso>
        <judgment>
            <header>Some header content</header>
            <judgmentBody>
                First replacement
                <p>Middle content</p>
                Second replacement
            </judgmentBody>
        </judgment>
    </akomaNtoso>"""
    assert processed_content == expected_xml


@mock_aws
def test_process_event_no_replacements_needed():
    s3 = boto3.client("s3")
    # Create all required buckets
    s3.create_bucket(Bucket="source-bucket")
    s3.create_bucket(Bucket="dest-bucket")
    s3.create_bucket(Bucket="replacements-bucket")

    input_xml = """<akomaNtoso>
        <judgment>
            <header>Some header content</header>
            <judgmentBody>
                <p>Content with no replacements needed</p>
            </judgmentBody>
        </judgment>
    </akomaNtoso>"""

    # Upload XML to source bucket
    s3.put_object(
        Bucket="source-bucket",
        Key="test.xml",
        Body=input_xml,
    )

    # Add empty replacements file
    s3.put_object(
        Bucket="replacements-bucket",
        Key="test.xml",
        Body="",  # Empty replacements file
    )
    sqs_record = {
        "messageAttributes": {
            "source_key": {"stringValue": "test.xml"},
            "source_bucket": {"stringValue": "source-bucket"},
        },
    }

    process_event(sqs_record, "dest-bucket", "source-bucket", "replacements-bucket")

    response = s3.get_object(Bucket="dest-bucket", Key="test.xml")
    processed_content = response["Body"].read().decode()

    assert processed_content == input_xml
