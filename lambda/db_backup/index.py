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
        print("Snapshot creating")

        # create a waiter for the DB cluster snapshot to be available
        waiter = rds.get_waiter('db_cluster_snapshot_available')

        # wait for the DB cluster snapshot to be available
        waiter.wait(DBClusterSnapshotIdentifier=snapshot_name)

        print(f'DB cluster snapshot {snapshot_name} is now available')

        # # Wait for snapshot to be created
        # rds.get_waiter("db_snapshot_available").wait(
        #     DBClusterSnapshotIdentifier=snapshot_name,
        #     IncludeShared=True,
        #     IncludePublic=False,
        # )
        # print("Snapshot is available")

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
