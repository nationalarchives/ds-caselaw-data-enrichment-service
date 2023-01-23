import json
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Create RDS and S3 clients
    rds = boto3.client("rds")
    s3 = boto3.client("s3")
    region = "eu-west-2"
    sts = boto3.client("sts")
    environment = os.getenv("environment")
    account_id = sts.get_caller_identity().get("Account")
    bucket = os.getenv("bucket-name")
    db = event["db-name"]
    now = datetime.now()
    date = now.strftime("%d-%m-%Y")

    try:
        # Take snapshot of RDS database
        print("Trying to create db snapshot")
        print("Time now", now)
        snapshot_name = "db-snapshot-" + date
        rds.create_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=snapshot_name, DBClusterIdentifier=db
        )
        print("Snapshot creating")

        # create a waiter for the DB cluster snapshot to be available
        waiter = rds.get_waiter("db_cluster_snapshot_available")

        # wait for the DB cluster snapshot to be available
        waiter.wait(DBClusterSnapshotIdentifier=snapshot_name)

        print(f"DB cluster snapshot {snapshot_name} is now available.")

        # Getting kms_key_id of snapshot
        response = rds.describe_db_cluster_snapshots(
            SnapshotType="Manual",
            IncludeShared=True,
            IncludePublic=False,
        )

        for snapshot in response["DBClusterSnapshots"]:
            if snapshot["DBClusterSnapshotIdentifier"] == snapshot_name:
                kms_key_id = snapshot["KmsKeyId"]
                print(kms_key_id)
                break

        print(
            f"DB cluster snapshot {snapshot_name} is now available. With {kms_key_id}"
        )

    except ClientError as e:
        print(e)

    try:
        # upload the object (file) to the bucket
        export_task_identifier = "db-backup-" + date
        rds.start_export_task(
            ExportTaskIdentifier=export_task_identifier,
            SourceArn=snapshot_name,
            S3BucketName=bucket,
            IamRoleArn="arn:aws:iam::{account_id}:role/tna-s3-tna-{environment}-db-backup",
            KmsKeyId=kms_key_id,
        )
    except ClientError as e:
        print(e)
