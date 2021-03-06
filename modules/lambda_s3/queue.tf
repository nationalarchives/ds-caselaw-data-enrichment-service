
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

resource "aws_sqs_queue_policy" "replacements-queue-policy" {
  queue_url = aws_sqs_queue.replacements-queue.id
  policy = <<POLICY
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

resource "aws_sqs_queue_policy" "replacements-abbreviations-queue-policy" {
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

resource "aws_sqs_queue" "validation_updates_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_error_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-error-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_dlq_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
#   redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.terraform_queue_deadletter.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}

resource "aws_sqs_queue" "validation_updates_error_dlq_queue" {
  name                      = "${local.name}-${local.environment}-validation-updates-error-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600 #max is 2 weeks or 1209600 secs
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled = true
#   redrive_policy            = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.terraform_queue_deadletter.arn}\",\"maxReceiveCount\":4}"

  tags = local.tags
}


resource "aws_sns_topic" "validation_updates" {
  name = "validation-updates-topic"
}

resource "aws_sns_topic" "validation_updates_error" {
  name = "validation-updates-error-topic"
}

resource "aws_sns_topic" "rules_update_error" {
  name = "rules-update-error-topic"
  display_name = "Rules Update Error"
}

resource "aws_sns_topic" "legislation_update_error" {
  name = "legislation-update-error-topic"
  display_name = "Legislation Update Error"
}

resource "aws_sns_topic" "extract_judgement_contents_error" {
  name = "extract-judgement-contents-error-topic"
  display_name = "Extract Judgement Contents Error"
}

resource "aws_sns_topic" "caselaw_detection_error" {
  name = "caselaw-detection-error-topic"
  display_name = "Case law Detection Error"
}

resource "aws_sns_topic" "legislation_detection_error" {
  name = "legislation-detection-error-topic"
  display_name = "Legislation Detection Error"
}

resource "aws_sns_topic" "abbreviation_detection_error" {
  name = "abbreviation-detection-error-topic"
  display_name = "Abbreviation Detection Error"
}

resource "aws_sns_topic" "make_replacements_error" {
  name = "make-replacements-error-topic"
  display_name = "Replacements Error"
}

resource "aws_sns_topic" "oblique_references_error" {
  name = "oblique-references-error-topic"
  display_name = "Oblique References Error"
}

resource "aws_sns_topic" "legislation_provisions_error" {
  name = "legislation-provisions-error-topic"
  display_name = "Legislation Provisions Error"
}

# Event source from SQS
resource "aws_lambda_event_source_mapping" "sqs_replacements_event_source_mapping_caselaw" {
  event_source_arn = aws_sqs_queue.replacement-caselaw-queue.arn
  enabled          = true
  function_name    = "${module.lambda-determine-replacements-legislation.lambda_function_arn}"
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_replacements_legislation_event_source_mapping" {
  event_source_arn = aws_sqs_queue.replacement-legislation-queue.arn
  enabled          = true
  function_name    = "${module.lambda-determine-replacements-abbreviations.lambda_function_arn}"
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "sqs_replacements_abbreviations_event_source_mapping" {
  event_source_arn = aws_sqs_queue.replacement-abbreviations-queue.arn
  enabled          = true
  function_name    = "${module.lambda-make-replacements.lambda_function_arn}"
  batch_size       = 1
}

resource "aws_cloudwatch_metric_alarm" "rules_update_error" {
  alarm_name          = "Manifest update error"
  alarm_description   = "Check if rules update lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-update-rules-processor"
	}
  alarm_actions = [aws_sns_topic.rules_update_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "legislation_update_error" {
  alarm_name          = "Legislation update error"
  alarm_description   = "Check if legislation update lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-update-legislation-table"
	}
  alarm_actions = [aws_sns_topic.legislation_update_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "extract-judgement-contents-error" {
  alarm_name          = "Extract judgement contents error"
  alarm_description   = "Check if extract judgement contents lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-extract-judgement-contents"
	}
  alarm_actions = [aws_sns_topic.extract_judgement_contents_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "caselaw_detection_error" {
  alarm_name          = "Case law detection error"
  alarm_description   = "Check if case law detection lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-determine-replacements-caselaw"
	}
  alarm_actions = [aws_sns_topic.caselaw_detection_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "legislation_detection_error" {
  alarm_name          = "Legislation detection error"
  alarm_description   = "Check if legislation detection lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-determine-replacements-legislation"
	}
  alarm_actions = [aws_sns_topic.legislation_detection_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "abbreviation_detection_error" {
  alarm_name          = "Abbreviation detection error"
  alarm_description   = "Check if abbreviation detection lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-determine-replacements-abbreviations"
	}
  alarm_actions = [aws_sns_topic.abbreviation_detection_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "make_replacements_error" {
  alarm_name          = "Replacements error"
  alarm_description   = "Check if replacements lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-make-replacements"
	}
  alarm_actions = [aws_sns_topic.make_replacements_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "oblique-references_error" {
  alarm_name          = "Oblique references error"
  alarm_description   = "Check if oblique references lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-determine-oblique-references"
	}
  alarm_actions = [aws_sns_topic.oblique_references_error.arn]
}

resource "aws_cloudwatch_metric_alarm" "legislation-provisions-error" {
  alarm_name          = "Legislation provisions error"
  alarm_description   = "Check if legislation provisions lambda throws an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  unit                = "Count"
  datapoints_to_alarm = "1"
  namespace           = "AWS/Lambda"
  period              = "180"
  statistic           = "Sum"
  threshold           = "0"
  dimensions          = {
		FunctionName = "${local.name}-${local.environment}-determine-legislation-provisions"
	}
  alarm_actions = [aws_sns_topic.legislation_provisions_error.arn]
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

resource "aws_sns_topic_subscription" "validation-error-email-niall-target" {
  topic_arn = aws_sns_topic.validation_updates_error.arn
  protocol  = "email"
  endpoint  = "niall.roche@mdrx.tech"
}

resource "aws_sns_topic_subscription" "validation-error-email-dan-target" {
  topic_arn = aws_sns_topic.validation_updates_error.arn
  protocol  = "email"
  endpoint  = "daniel.hoadley@mishcon.com"
}

resource "aws_sns_topic_subscription" "rules-error-email-editha-target" {
  topic_arn = aws_sns_topic.rules_update_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "legislation-update-error-email-editha-target" {
  topic_arn = aws_sns_topic.legislation_update_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "extract_judgement_contents_error-email-editha-target" {
  topic_arn = aws_sns_topic.extract_judgement_contents_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "caselaw-detection-error-email-editha-target" {
  topic_arn = aws_sns_topic.caselaw_detection_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "legislation-detection-error-email-editha-target" {
  topic_arn = aws_sns_topic.legislation_detection_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "abbreviation-detection-error-email-editha-target" {
  topic_arn = aws_sns_topic.abbreviation_detection_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "make-replacements-error-email-editha-target" {
  topic_arn = aws_sns_topic.make_replacements_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "oblique-references-error-email-editha-target" {
  topic_arn = aws_sns_topic.oblique_references_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "legislation-provisions-error-email-editha-target" {
  topic_arn = aws_sns_topic.legislation_provisions_error.arn
  protocol  = "email"
  endpoint  = "editha.nemsic@mishcon.com"
}

resource "aws_sns_topic_subscription" "rules-error-email-dan-target" {
  topic_arn = aws_sns_topic.rules_update_error.arn
  protocol  = "email"
  endpoint  = "daniel.hoadley@mishcon.com"
}