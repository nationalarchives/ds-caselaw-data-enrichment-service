import os

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Create RDS and S3 clients
    rds = boto3.client("rds")
    s3 = boto3.client("s3")
    bucket = os.getenv("bucket-name")
    db = event["db-name"]

    try:
        # Take snapshot of RDS database
        snapshot_name = "db-snapshot-" + event["time"]
        rds.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_name, DBInstanceIdentifier=db
        )

        # Wait for snapshot to be created
        rds.get_waiter("db_snapshot_available").wait(DBSnapshotIdentifier=snapshot_name)
    except ClientError as e:
        print(e)

    try:
        # Copy snapshot to S3 bucket
        s3.copy_db_snapshot(
            SourceDBSnapshotIdentifier=snapshot_name,
            TargetBucket=bucket,
            TargetDBSnapshotIdentifier=snapshot_name,
        )
        print("Copied snapshot to S3")
    except ClientError as e:
        print(e)
