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
        waiter = rds.get_waiter("db_cluster_snapshot_available")

        # wait for the DB cluster snapshot to be available
        waiter.wait(DBClusterSnapshotIdentifier=snapshot_name)

        print(f"DB cluster snapshot {snapshot_name} is now available")

    except ClientError as e:
        print(e)

    try:
        # upload the object (file) to the bucket
        s3.put_object(Bucket=bucket, Key=snapshot_name, Body=open(snapshot_name, "rb"))

        print(f"{snapshot_name} has been successfully uploaded to {bucket}")
    except ClientError as e:
        print(e)
