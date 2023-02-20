URI=${1:-ewca/civ/2023/105}
awslocal sqs send-message \
  --queue-url http://localhost:4566/000000000000/fetch-xml-queue \
  --message-body "{\"Message\": \"{\\\"status\\\": \\\"published\\\", \\\"uri_reference\\\": \\\"$URI\\\"}\"}"
