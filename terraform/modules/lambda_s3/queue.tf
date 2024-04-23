resource "aws_sqs_queue" "replacement-caselaw-queue" {
  name                       = "${local.name}-${local.environment}-replacement-caselaw-event-notification-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy             = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.replacements-caselaw_dlq_queue.arn}\",\"maxReceiveCount\":4}"

}

resource "aws_sqs_queue_policy" "replacement-caselaw-queue-policy" {
  queue_url = aws_sqs_queue.replacement-caselaw-queue.id
  policy    = <<POLICY
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
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "replacements_dlq_queue" {
  name                      = "${local.name}-${local.environment}-replacements-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "replacements-queue" {
  name                       = "${local.name}-${local.environment}-replacements-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.replacements_dlq_queue.arn,
    maxReceiveCount     = 4,
  })

  tags = local.tags
}

resource "aws_sqs_queue_policy" "replacements-queue-policy" {
  queue_url = aws_sqs_queue.replacements-queue.id
  policy    = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.replacements-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-make-replacements.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}

resource "aws_sqs_queue" "replacement-legislation-queue" {
  name                       = "${local.name}-${local.environment}-replacement-legislation-event-notification-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.replacements-legislation_dlq_queue.arn,
    maxReceiveCount     = 4,
  })
}

resource "aws_sqs_queue_policy" "replacement-legislation-queue-policy" {
  queue_url = aws_sqs_queue.replacement-legislation-queue.id
  policy    = <<POLICY
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
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "replacement-abbreviations-queue" {
  name                       = "${local.name}-${local.environment}-replacement-abbreviations-event-notification-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.replacements-abbreviations_dlq_queue.arn,
    maxReceiveCount     = 4,
  })
}

resource "aws_sqs_queue_policy" "replacements-abbreviations-queue-policy" {
  queue_url = aws_sqs_queue.replacement-abbreviations-queue.id
  policy    = <<POLICY
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
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation-queue" {
  name = "${local.name}-${local.environment}-validation-event-notification-queue"

  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.validation_dlq_queue.arn,
    maxReceiveCount     = 4,
  })

  tags = local.tags
}

resource "aws_sqs_queue_policy" "validation-queue-policy" {
  queue_url = aws_sqs_queue.validation-queue.id
  policy    = <<POLICY
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
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_error_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-error-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_dlq_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_error_dlq_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-error-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue" "xml-validated-queue" {
  name                       = "${local.name}-${local.environment}-xml-validated-notification-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.xml-validated_dlq_queue.arn,
    maxReceiveCount     = 4,
  })
}

resource "aws_sqs_queue_policy" "xml-validated-queue-policy" {
  queue_url = aws_sqs_queue.xml-validated-queue.id
  policy    = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.xml-validated-queue.arn}",
      "Condition": {
        "ArnEquals": { "aws:SourceArn": "${module.lambda-validate-replacements.lambda_function_arn}" }
      }
    }
  ]
}
POLICY
}

resource "aws_sqs_queue" "xml-validated_dlq_queue" {
  name                      = "${local.name}-${local.environment}-xml-validated-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}


resource "aws_sns_topic" "validation_updates" {
  name = "validation-updates-topic"
}

resource "aws_sns_topic" "validation_updates_error" {
  name = "validation-updates-error-topic"
}

resource "aws_sns_topic" "enrichment_error_alerts" {
  name         = "enrichment-error-topic"
  display_name = "Enrichment Error"
}

# Event source from SQS
resource "aws_lambda_event_source_mapping" "sqs_replacements_event_source_mapping_caselaw" {
  event_source_arn = aws_sqs_queue.replacement-caselaw-queue.arn
  enabled          = true
  function_name    = module.lambda-determine-replacements-legislation.lambda_function_arn
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_replacements_legislation_event_source_mapping" {
  event_source_arn = aws_sqs_queue.replacement-legislation-queue.arn
  enabled          = true
  function_name    = module.lambda-determine-replacements-abbreviations.lambda_function_arn
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_replacements_abbreviations_event_source_mapping" {
  event_source_arn = aws_sqs_queue.replacement-abbreviations-queue.arn
  enabled          = true
  function_name    = module.lambda-make-replacements.lambda_function_arn
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_validated_xml_event_source_mapping" {
  event_source_arn = aws_sqs_queue.xml-validated-queue.arn
  enabled          = true
  function_name    = module.lambda-push-enriched-xml.lambda_function_arn
  batch_size       = 1
}


locals {
  lambda_function_names = [
    for function_name in [
      "fetch-xml",
      "extract-judgement-contents",
      "determine-replacements-caselaw",
      "determine-replacements-legislation",
      "make-replacements",
      "determine-replacements-abbreviations",
      "determine-oblique-references",
      "determine-legislation-provisions",
      "xml-validate",
      "push-enriched-xml",
      "db-backup",
      "update-rules-processor",
      "update-legislation-table"
    ] : "${local.name}-${local.environment}-${function_name}"
  ]
}


resource "aws_cloudwatch_metric_alarm" "lambda_errors_alarm" {
  count               = length(local.lambda_function_names)
  alarm_description   = "${local.lambda_function_names[count.index]} Error"
  alarm_name          = "${local.lambda_function_names[count.index]} Error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions = {
    FunctionName = local.lambda_function_names[count.index]
  }
  alarm_actions = [aws_sns_topic.enrichment_error_alerts.arn]
}


resource "aws_sns_topic_subscription" "validation_updates_sqs_target" {
  topic_arn = aws_sns_topic.validation_updates.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.validation_updates_queue.arn
}

resource "aws_sns_topic_subscription" "validation_updates_error_sqs_target" {
  topic_arn = aws_sns_topic.validation_updates_error.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.validation_updates_error_queue.arn
}

resource "aws_sns_topic_subscription" "enrichment_error_alert_email_subscriptions" {
  count     = length(local.error_alert_emails_list)
  topic_arn = aws_sns_topic.enrichment_error_alerts.arn
  protocol  = "email"
  endpoint  = local.error_alert_emails_list[count.index]
}


resource "aws_sqs_queue" "fetch_xml_queue" {
  name                       = "${local.name}-${local.environment}-fetch-xml-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.fetch_xml_dlq_queue.arn,
    maxReceiveCount     = 4,
  })

  tags = local.tags
}

resource "aws_sqs_queue" "fetch_xml_dlq_queue" {
  name                      = "${local.name}-${local.environment}-fetch-xml-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue_policy" "fetch_xml_queue_policy" {
  queue_url = aws_sqs_queue.fetch_xml_queue.id
  policy    = data.aws_iam_policy_document.sqs_policy_fetch_xml.json
}


resource "aws_lambda_event_source_mapping" "sqs_replacements_fetch_xml_event_source_mapping" {
  event_source_arn = aws_sqs_queue.fetch_xml_queue.arn
  enabled          = true
  function_name    = module.lambda-fetch-xml.lambda_function_arn
  batch_size       = 1
}

resource "aws_sns_topic_subscription" "fetch_xml_queue_subscription" {
  count               = var.environment != "production" ? 1 : 0
  topic_arn           = "arn:aws:sns:eu-west-2:626206937213:caselaw-stg-judgment-updated"
  protocol            = "sqs"
  endpoint            = aws_sqs_queue.fetch_xml_queue.arn
  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({
    trigger_enrichment = [
      {
        exists = true
      }
    ]
  })
}

resource "aws_sns_topic_subscription" "fetch_xml_queue_subscription_prod" {
  count               = var.environment == "production" ? 1 : 0
  topic_arn           = "arn:aws:sns:eu-west-2:276505630421:caselaw-judgment-updated"
  protocol            = "sqs"
  endpoint            = aws_sqs_queue.fetch_xml_queue.arn
  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({
    trigger_enrichment = [
      {
        exists = true
      }
    ]
  })
}
