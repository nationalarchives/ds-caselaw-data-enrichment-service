import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Create RDS and S3 clients
    rds = boto3.client("rds")
    s3 = boto3.client("s3")
    bucket = os.getenv("bucket-name")
    db = event["db-name"]
    now = datetime.now()
    date = now.strftime("%d-%m-%Y")

    try:
        # Take snapshot of RDS database
        print("Trying to create db snapshot")
        snapshot_name = "db-snapshot-" + date
        rds.create_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=snapshot_name, DBClusterIdentifier=db
        )

        # Wait for snapshot to be created
        rds.get_waiter("db_snapshot_available").wait(DBSnapshotIdentifier=snapshot_name, IncludeShared=True, IncludePublic=False)
        print("Snapshot created")
    except ClientError as e:
        print(e)

    try:
        # Copy snapshot to S3 bucket
        print("Attempting to upload snapshot to S3.")
        s3.copy_db_snapshot(
            SourceDBSnapshotIdentifier=snapshot_name,
            TargetBucket=bucket,
            TargetDBSnapshotIdentifier=snapshot_name,
        )
        print("Copied snapshot to S3")
    except ClientError as e:
        print(e)
