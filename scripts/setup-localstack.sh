source .env

awslocal iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document file://localstack/example_trust_policy.json

awslocal lambda create-function \
  --function-name fetch-xml \
  --zip-file fileb://dist/fetch_xml.zip \
  --handler fetch_xml/index.handler \
  --runtime python3.9 \
  --environment "Variables={AWS_ENDPOINT_URL=$AWS_ENDPOINT_URL,API_PASSWORD=$API_PASSWORD,API_USERNAME=$API_USERNAME,DEST_BUCKET_NAME=$BUCKET_XML_ORIGINAL,ENVIRONMENT=$ENVIRONMENT}" \
  --role arn:aws:iam::000000000000:role/lambda-role

awslocal sqs create-queue --queue-name fetch-xml-queue  # triggers fetch_xml
awslocal sqs set-queue-attributes --queue-url http://localhost:4566/000000000000/fetch-xml-queue --attributes "{\"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\": \\\"x\\\", \\\"maxReceiveCount\\\": 1}\"}"



awslocal s3api create-bucket --bucket $BUCKET_XML_ORIGINAL

awslocal lambda create-event-source-mapping \
  --function-name fetch-xml \
  --event-source-arn arn:aws:sqs:us-east-1:000000000000:fetch-xml-queue

# awslocal sns create-topic \
#   --name judgments \
#   --attributes consignment-reference=string,s3-folder-url=string,consignment-type=string,number-of-retries=number

# awslocal sns subscribe \
#   --topic-arn arn:aws:sns:us-east-1:000000000000:judgments \
#   --protocol lambda \
#   --notification-endpoint arn:aws:lambda:us-east-1:000000000000:function:te-lambda

# awslocal iam create-role \
#   --role-name lambda-role \
#   --assume-role-policy-document file://aws_examples/example_trust_policy.json

# awslocal lambda create-function \
#   --function-name te-lambda \
#   --zip-file fileb://dist/lambda.zip \
#   --handler ds-caselaw-ingester/lambda_function.handler \
#   --runtime python3.9 \
#   --environment "Variables={MARKLOGIC_HOST=$MARKLOGIC_HOST,MARKLOGIC_USER=$MARKLOGIC_USER,MARKLOGIC_PASSWORD=$MARKLOGIC_PASSWORD,AWS_BUCKET_NAME=$AWS_BUCKET_NAME,AWS_SECRET_KEY=$AWS_SECRET_KEY,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID,AWS_ENDPOINT_URL=$AWS_ENDPOINT_URL,SQS_QUEUE_URL=$SQS_QUEUE_URL,ROLLBAR_TOKEN=$ROLLBAR_TOKEN,ROLLBAR_ENV=$ROLLBAR_ENV,NOTIFY_API_KEY=$NOTIFY_API_KEY,NOTIFY_EDITORIAL_ADDRESS=$NOTIFY_EDITORIAL_ADDRESS,NOTIFY_NEW_JUDGMENT_TEMPLATE_ID=$NOTIFY_NEW_JUDGMENT_TEMPLATE_ID,EDITORIAL_UI_BASE_URL=$EDITORIAL_UI_BASE_URL,PUBLIC_ASSET_BUCKET=$PUBLIC_ASSET_BUCKET}" \
#   --role arn:aws:iam::000000000000:role/lambda-role \

# awslocal sns create-topic \
#   --name judgments \
#   --attributes consignment-reference=string,s3-folder-url=string,consignment-type=string,number-of-retries=number

# awslocal sns subscribe \
#   --topic-arn arn:aws:sns:us-east-1:000000000000:judgments \
#   --protocol lambda \
#   --notification-endpoint arn:aws:lambda:us-east-1:000000000000:function:te-lambda

# awslocal s3api create-bucket \
#   --bucket te-editorial-out-int

# awslocal s3api create-bucket \
#   --bucket judgments-original-versions

# awslocal s3api create-bucket \
#   --bucket public-asset-bucket

# if [ -n "$1" ]; then
#   awslocal s3 cp $1 s3://te-editorial-out-int
# else
#   awslocal s3 cp aws_examples/s3/te-editorial-out-int/TDR-2022-DNWR.tar.gz s3://te-editorial-out-int
# fi

# awslocal sqs create-queue --queue-name retry-queue
