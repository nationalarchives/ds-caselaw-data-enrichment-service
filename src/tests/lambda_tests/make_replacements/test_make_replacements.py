import boto3
from moto import mock_aws

from lambdas.make_replacements.index import process_event


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

    expected_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<akomaNtoso>"
        "<judgment>"
        "<header>Some header content</header>"
        "<judgmentBody>"
        "<origin-ref>First replacement</origin-ref>"
        "<p>Middle content</p>"
        "<origin-ref>Second replacement</origin-ref>"
        "</judgmentBody>"
        "</judgment>"
        "</akomaNtoso>"
    )
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
