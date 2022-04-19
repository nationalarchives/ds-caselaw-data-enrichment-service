# # SQS queue
# resource "aws_sqs_queue" "queue" {
#   name = "${var.app_env}-s3-event-notification-queue"

#   policy = <<POLICY
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Principal": "*",
#       "Action": "sqs:SendMessage",
#       "Resource": "arn:aws:sqs:*:*:${var.app_env}-s3-event-notification-queue",
#       "Condition": {
#         "ArnEquals": { "aws:SourceArn": "${aws_s3_bucket.bucket.arn}" }
#       }
#     }
#   ]
# }
# POLICY
# }

resource "aws_sqs_queue" "replacement-caselaw-queue" {
  name = "${local.name}-${local.environment}-replacement-caselaw-event-notification-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
  redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.replacements-caselaw_dlq_queue.arn}\",\"maxReceiveCount\":4}"

}

resource "aws_sqs_queue_policy" "replacement-caselaw-queue-policy" {
  queue_url = aws_sqs_queue.replacement-caselaw-queue.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.replacement-caselaw-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-determine-replacements-caselaw.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}

resource "aws_sqs_queue" "replacements-caselaw_dlq_queue" {
  name                      = "${local.name}-${local.environment}-replacements-caselaw-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
#   redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.terraform_queue_deadletter.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}



resource "aws_sqs_queue" "replacements_dlq_queue" {
  name                      = "${local.name}-${local.environment}-replacements-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
#   redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.terraform_queue_deadletter.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}

resource "aws_sqs_queue" "replacements-queue" {
  name                      = "${local.name}-${local.environment}-replacements-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
  redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.replacements_dlq_queue.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}

resource "aws_sqs_queue_policy" "replacement-queue-policy" {
  queue_url = aws_sqs_queue.replacement-queue.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.replacement-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-make-replacements.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}




resource "aws_sqs_queue" "replacement-legislation-queue" {
  name = "${local.name}-${local.environment}-replacement-legislation-event-notification-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
  redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.replacements-legislation_dlq_queue.arn}\",\"maxReceiveCount\":4}"

}

resource "aws_sqs_queue_policy" "replacement-legislation-queue-policy" {
  queue_url = aws_sqs_queue.replacement-legislation-queue.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.replacement-legislation-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-determine-replacements-legislation.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}

resource "aws_sqs_queue" "replacements-legislation_dlq_queue" {
  name                      = "${local.name}-${local.environment}-replacements-legislation-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
#   redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.terraform_queue_deadletter.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}





resource "aws_sqs_queue" "replacement-abbreviations-queue" {
  name = "${local.name}-${local.environment}-replacement-abbreviations-event-notification-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
  redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.replacements-abbreviations_dlq_queue.arn}\",\"maxReceiveCount\":4}"

}

resource "aws_sqs_queue_policy" "replacement-abbreviations-queue-policy" {
  queue_url = aws_sqs_queue.replacement-abbreviations-queue.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.replacement-abbreviations-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-determine-replacements-abbreviations.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}

resource "aws_sqs_queue" "replacements-abbreviations_dlq_queue" {
  name                      = "${local.name}-${local.environment}-replacements-abbreviations-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
#   redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.terraform_queue_deadletter.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}



resource "aws_sqs_queue" "validation-queue" {
  name = "${local.name}-${local.environment}-validation-event-notification-queue"

  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
  redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.validation_dlq_queue.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}

resource "aws_sqs_queue_policy" "validation-queue-policy" {
  queue_url = aws_sqs_queue.validation-queue.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.validation-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-validate-replacements.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}

resource "aws_sqs_queue" "validation_dlq_queue" {
  name                      = "${local.name}-${local.environment}-validation-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true

  tags = local.tags
}




# resource "aws_sqs_queue_policy" "validated-queue-policy" {
#   queue_url = aws_sqs_queue.validated-queue.id
#   policy = <<POLICY
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Principal": "*",
#       "Action": "sqs:SendMessage",
#       "Resource": "${aws_sqs_queue.validated-queue.arn}",
#       "Condition": {
#         "ArnEquals": { "aws:SourceArn": "${module.lambda-validate-replacements.lambda_function_arn}" }
#       }
#     }
#   ]
# }
# POLICY
# }

# resource "aws_sqs_queue" "validated_dlq_queue" {
#   name                      = "${local.name}-${local.environment}-validated-dlq-queue"
#   delay_seconds             = 90
#   max_message_size          = 2048
#   message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
#   receive_wait_time_seconds = 10
#   sqs_managed_sse_enabled = true

#   tags = local.tags
# }

# Event source from SQS

# TODO put back in

# resource "aws_lambda_event_source_mapping" "sqs_replacements_event_source_mapping" {
#   event_source_arn = aws_sqs_queue.replacements_queue.arn
#   enabled          = true
# #   function_name    = aws_lambda_function.lambda-make-replacements.arn
# #   function_name    = module.lambda-make-replacements.arn
#   function_name    = module.lambda-make-replacements.lambda_function_arn
# #   function_name    = "arn:aws:lambda:eu-west-1:849689169827:function:tna-s3-development-ucl-make-replacements"
# #   function_name    = "${module.lambda-make-replacements.arn}"
#   batch_size       = 1
# }

# Event source from SQS
resource "aws_lambda_event_source_mapping" "sqs_replacements_event_source_mapping_caselaw" {
  event_source_arn = aws_sqs_queue.replacement-caselaw-queue.arn
  enabled          = true
  # function_name    = "${module.lambda-make-replacements.lambda_function_arn}"
  function_name    = "${module.lambda-determine-replacements-legislation.lambda_function_arn}"
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_replacements_legislation_event_source_mapping" {
  event_source_arn = aws_sqs_queue.replacement-legislation-queue.arn
  enabled          = true
  # function_name    = "${module.lambda-make-replacements.lambda_function_arn}"
  function_name    = "${module.lambda-determine-replacements-abbreviations.lambda_function_arn}"
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_replacements_abbreviations_event_source_mapping" {
  event_source_arn = aws_sqs_queue.replacement-abbreviations-queue.arn
  enabled          = true
  function_name    = "${module.lambda-make-replacements.lambda_function_arn}"
  # function_name    = "${module.lambda-determine-replacements-abbreviation.lambda_function_arn}"
  batch_size       = 1
}

