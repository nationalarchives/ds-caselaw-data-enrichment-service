import os
import unittest

import boto3
import mock
import pytest
from moto import mock_s3

# from lambda_function import *


test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
	<level>
	  <content>
	    <p style="margin-right:0.00in;text-indent:0.00in">the properties of golf clubs, the ISP is not, as the CMA decided and the CAT held, objectively justified. </p>
	  </content>
	</level>
</akomaNtoso>"""

test_s3_event = {
    "Records": [
        {"s3": {"bucket": {"name": "test_bucket"}, "object": {"key": "test_data.xml"}}}
    ]
}

# test_sqs_event = {
#     "Records": [{
#         "body": json.dumps({
#             "user_id": "B9B3022F98Fjvjs83AB8/80C185D8",
#             "updated_timstamp": "2020-03-03T00:50:47"
#         })
#     }]}

# schema_bucket = validate_env_variable("SCHEMA_BUCKET_NAME")
# schema_key = validate_env_variable("SCHEMA_BUCKET_KEY")

# def s3_client_with_assessments_bucket():
#     conn = boto3.client("s3", region_name="eu-west-2")
#     conn.create_bucket(
#         Bucket="csx-assessments",
#         CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
#     )
#     return conn


class MyModel(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def save(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.put_object(Bucket="mybucket", Key=self.name, Body=self.value)


# @mock_s3
@mock.patch.dict(
    os.environ,
    {"VALIDATE_USING_SCHEMA": "false", "VALIDATE_USING_DTD": "false"},
    clear=True,
)
class TestXMLValidate(unittest.TestCase):
    # def setUp(self):
    #     # self.nlp, self.db_conn = set_up()
    #     print("setUp")

    # @pytest.fixture(scope='function')
    # def aws_credentials():
    #     """Mocked AWS Credentials for moto."""
    #     os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    #     os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    #     os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    #     os.environ['AWS_SESSION_TOKEN'] = 'testing'
    #     os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    # @pytest.fixture(scope='function')
    # def s3(aws_credentials):
    #     with mock_s3():
    #         yield boto3.client('s3', region_name='us-east-1')

    # client = boto3.client("s3")
    # s3 = boto3.resource("s3")

    @mock_s3
    def test_my_model_save(self):
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket="mybucket")

        model_instance = MyModel("steve", "is awesome")
        model_instance.save()

        body = conn.Object("mybucket", "steve").get()["Body"].read().decode("utf-8")

        assert body == "is awesome"

    # @mock_s3
    # @mock.patch.dict(os.environ, {'VALIDATE_USING_SCHEMA': "False",'VALIDATE_USING_DTD': "False"}, clear=True)
    # @mock.patch.dict(os.environ, {'AWS_ACCESS_KEY_ID':'fake'}, clear=True)
    @mock_s3
    # def test_lambda_handler(self):
    def test_process_event(self):
        # monkeypatch.setenv("VALIDATE_USING_SCHEMA", "False")

        # set up test bucket
        # s3 = s3_client_with_assessments_bucket()
        # uploaded_file = s3.get_object(
        #     Bucket="csx-assessments", Key="11int22-assessment.pdf"
        # )
        # assert uploaded_file["Body"].read() == b"this is a test"

        # s3_client = boto3.client('s3')

        # from moto.core import patch_client, patch_resource
        # patch_client(s3_client)
        # patch_resource(s3)

        # s3_client = self.s3

        # s3 = boto3.client('s3', region_name='us-east-1')

        # conn = boto3.resource('s3', region_name='us-east-1')
        conn = boto3.client("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        # conn.create_bucket(Bucket=test_bucket_name)
        # bucket = conn.create_bucket(Bucket='mybucket')

        test_bucket_name = "test_bucket"
        test_data = b"col_1,col_2\n1,2\n3,4\n"

        # object = conn.Object(test_bucket_name, f'test_data.xml')
        # object.put(Body=test_data)

        bucket = conn.create_bucket(
            Bucket=test_bucket_name,
            # CreateBucketConfiguration={"LocationConstraint": "us-east-1"}
        )
        # bucket.put(Body=test_data)

        conn.put_object(
            Bucket=test_bucket_name,
            Key="test_data.xml",
            Body=test_xml_content,
        )

        # conn.put_object(Body=test_data, Bucket=test_bucket_name, Key=f'example/s3/path/key/test_data.xml')

        # conn.put_object(Key=f'example/s3/path/key/test_data.xml', Value=test_data)

        # from lambdas.xml_validate.index import handler
        from lambdas.xml_validate.index import process_event

        process_event(test_s3_event.get("Records")[0], conn)

    #     s3.create_bucket(Bucket=test_bucket_name, CreateBucketConfiguration={
    # 'LocationConstraint': 'us-east-1'})
    #     s3.put_object(Body=test_data, Bucket=test_bucket_name, Key=f'example/s3/path/key/test_data.xml')

    # try:
    # response = handler(event=test_sqs_event, context={})
    # except Exception as e:
    #     print(e)

    # assert response == True


if __name__ == "__main__":
    unittest.main()
