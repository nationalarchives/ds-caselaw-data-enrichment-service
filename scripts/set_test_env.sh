#!/usr/bin/env bash
# export S3BUCKET=s3://ucldetf-s3-sqs-demo-bucket.s3.eu-west-1.amazonaws.com
# export S3BUCKET=s3://ucldetf-s3-sqs-demo-bucket
export BUCKET_ENVIRONMENT=ucl-tna-s3-development
export SOURCE_S3_BUCKET=s3://${BUCKET_ENVIRONMENT}-xml-original-bucket
export DESTINATION_S3_BUCKET=s3://${BUCKET_ENVIRONMENT}-text-content-bucket
export TEST_FOLDER_LOCAL=tests/
export TEST_FILE=testfile.xml
export TEST_FILE_REPLACED=testfile.txt
export TEST_FILE_CONTENTS="Some File Contents\nwith more content\nin it on new lines"
export AWS_PROFILE=ucl