import os
import unittest

import boto3
import mock
from moto import mock_s3

# from lambdas.extract_judgement_contents.index import *
# _function import *

test_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso>
        <level>
          <content>
            <p style="margin-right:0.00in;text-indent:0.00in">the properties of golf clubs, the ISP is not, as the CMA decided and the CAT held, objectively justified. </p>
          </content>
        </level>
</akomaNtoso>"""

test_extracted_xml_content = "the properties of golf clubs, the ISP is not, as the CMA decided and the CAT held, objectively justified."
# test_extracted_xml_content = """<p style="margin-right:0.00in;text-indent:0.00in">the properties of golf clubs, the ISP is not, as the CMA decided and the CAT held, objectively justified. </p>"""

test_s3_event = {
    "Records": [
        {
            "s3": {
                "bucket": {"name": "test_bucket"},
                "object": {"key": "example/s3/path/key/test_data.xml"},
            }
        }
    ]
}

# test_sqs_event = {
#     "Records": [{
#         "body": json.dumps({
#             "user_id": "B9B3022F98Fjvjs83AB8/80C185D8",
#             "updated_timstamp": "2020-03-03T00:50:47"
#         })
#     }]}

test_bucket_destination_name = "test_bucket_destination_name"


@mock.patch.dict(
    os.environ, {"DEST_BUCKET_NAME": test_bucket_destination_name}, clear=True
)
class TestExtractJudgement(unittest.TestCase):
    # def setUp(self):
    #     print("setUp")

    @mock_s3
    # @mock.patch.dict(os.environ, {'DEST_BUCKET_NAME': test_bucket_destination_name}, clear=True)
    def test_extract_text_content(self):
        # monkeypatch.setenv("DEST_BUCKET_NAME", test_bucket_destination_name)
        from lambdas.extract_judgement_contents.index import (
            extract_text_content,
        )

        extracted_xml_content = extract_text_content(test_xml_content)
        self.assertEqual(extracted_xml_content, test_extracted_xml_content)

    @mock_s3
    def test_lambda_handler(self):
        from lambdas.extract_judgement_contents.index import handler

        conn = boto3.client("s3", region_name="us-east-1")
        test_bucket_name = "test_bucket"
        # test_data = b'col_1,col_2\n1,2\n3,4\n'

        conn.create_bucket(Bucket=test_bucket_name)
        conn.create_bucket(Bucket=test_bucket_destination_name)

        conn.put_object(
            Bucket=test_bucket_name,
            Key=f"example/s3/path/key/test_data.xml",
            Body=test_xml_content,
        )

        handler(event=test_s3_event, context={})
        #         body = conn.Object('mybucket', 'steve').get()[
        # 'Body'].read().decode("utf-8")
        # test_bucket_destination_name/example/s3/path/key/test_data.txt
        uploaded_content = conn.get_object(
            Bucket=test_bucket_destination_name,
            Key=f"example/s3/path/key/test_data.txt",
        )
        # print(uploaded_content)
        cleaned_content = uploaded_content["Body"].read().decode("utf-8")
        # print(cleaned_content)
        cleaned_content = cleaned_content.replace("\\n\\t", "")
        cleaned_content = cleaned_content.strip()
        self.assertEqual(cleaned_content, test_extracted_xml_content)
        # except Exception as e:
        #     print(e)

        # assert True == True

    # def tearDown(self):
    #     print("tearDown")
    #     # close_connection(self.db_conn)


if __name__ == "__main__":
    unittest.main()
