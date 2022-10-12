# Replace this file with functional code rather than one that just lists the S3 buckets.
import boto3
from botocore.exceptions import ClientError

def handler(event, context):
    try:
        client = boto3.client("s3")
        response = client.list_buckets()
        buckets = []
        for bucket in response['Buckets']:
            buckets += {bucket["Name"]}

    except ClientError:
        print("Error")
        raise
    else:
        return
