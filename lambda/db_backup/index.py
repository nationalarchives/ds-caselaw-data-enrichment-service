from datetime import datetime

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Create RDS and S3 clients
    rds = boto3.client("rds")
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

        # Confirming snapshot is there
        response = rds.describe_db_cluster_snapshots(
            SnapshotType="Manual",
            IncludeShared=True,
            IncludePublic=False,
        )

        for snapshot in response["DBClusterSnapshots"]:
            if snapshot["DBClusterSnapshotIdentifier"] == snapshot_name:
                print(f"DB cluster snapshot {snapshot_name} is now available.")
                break
            else:
                print("Could not find snapshot")

    except ClientError as e:
        print(e)
