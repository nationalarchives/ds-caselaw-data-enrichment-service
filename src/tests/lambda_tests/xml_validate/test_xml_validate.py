import os
import unittest
from unittest import mock

import boto3
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventRecord
from moto import mock_aws

test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
        <level>
          <content>
            <p style="margin-right:0.00in;text-indent:0.00in">the properties of golf clubs, the ISP is not, as the CMA decided and the CAT held, objectively justified. </p>
          </content>
        </level>
</akomaNtoso>"""

test_s3_event_record = S3EventRecord({"s3": {"bucket": {"name": "test_bucket"}, "object": {"key": "test_data.xml"}}})


class MyModel:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def save(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.put_object(Bucket="mybucket", Key=self.name, Body=self.value)


@mock.patch.dict(
    os.environ,
    {"VALIDATE_USING_SCHEMA": "false", "VALIDATE_USING_DTD": "false"},
    clear=True,
)
class TestXMLValidate(unittest.TestCase):
    @mock_aws
    def test_my_model_save(self):
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket="mybucket")

        model_instance = MyModel("steve", "is awesome")
        model_instance.save()

        body = conn.Object("mybucket", "steve").get()["Body"].read().decode("utf-8")

        assert body == "is awesome"

    @mock_aws
    @mock.patch.dict(
        os.environ,
        {
            "DEST_BUCKET_NAME": "DEST_BUCKET_NAME",
            "VCITE_BUCKET": "VCITE_BUCKET",
            "VCITE_ENRICHED_BUCKET": "VCITE_ENRICHED_BUCKET",
            "DEST_ERROR_TOPIC_NAME": "DEST_ERROR_TOPIC_NAME",
            "DEST_TOPIC_NAME": "DEST_TOPIC_NAME",
            "VALIDATE_USING_SCHEMA": "0",
            "DEST_QUEUE": "DEST_QUEUE",
            "AWS_DEFAULT_REGION": "eu-west-2",
        },
    )
    def test_process_event(self):
        conn = boto3.client("s3", region_name="us-east-1")
        test_bucket_name = "test_bucket"

        conn.create_bucket(
            Bucket=test_bucket_name,
        )

        conn.put_object(
            Bucket=test_bucket_name,
            Key="test_data.xml",
            Body=test_xml_content,
        )

        from lambdas.xml_validate.index import process_event

        process_event(test_s3_event_record)


if __name__ == "__main__":
    unittest.main()
