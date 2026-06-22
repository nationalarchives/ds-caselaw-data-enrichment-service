# ============================================================
# ENRICHMENT QUEUE  (replaces the old fetch_xml_queue chain)
# ============================================================

resource "aws_sqs_queue" "enrichment_queue" {
  name                       = "${local.name}-${local.environment}-enrichment-queue"
  delay_seconds              = 90
  max_message_size           = 2048
  visibility_timeout_seconds = 900
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 10
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.enrichment_dlq_queue.arn
    maxReceiveCount     = 4
  })
  tags = local.tags
}

resource "aws_sqs_queue" "enrichment_dlq_queue" {
  name                      = "${local.name}-${local.environment}-enrichment-dlq-queue"
  delay_seconds             = 90
  max_message_size          = 2048
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 10
  sqs_managed_sse_enabled   = true
  tags                      = local.tags
}

resource "aws_sqs_queue_policy" "enrichment_queue_policy" {
  queue_url = aws_sqs_queue.enrichment_queue.id
  policy    = data.aws_iam_policy_document.sqs_policy_enrichment_queue.json
}

# Subscribe to staging SNS topic (non-production)
resource "aws_sns_topic_subscription" "enrichment_queue_subscription" {
  count               = var.environment != "production" ? 1 : 0
  topic_arn           = "arn:aws:sns:eu-west-2:626206937213:caselaw-stg-judgment-updated"
  protocol            = "sqs"
  endpoint            = aws_sqs_queue.enrichment_queue.arn
  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({
    trigger_enrichment = [{ exists = true }]
  })
}

# Subscribe to production SNS topic
resource "aws_sns_topic_subscription" "enrichment_queue_subscription_prod" {
  count               = var.environment == "production" ? 1 : 0
  topic_arn           = "arn:aws:sns:eu-west-2:276505630421:caselaw-judgment-updated"
  protocol            = "sqs"
  endpoint            = aws_sqs_queue.enrichment_queue.arn
  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({
    trigger_enrichment = [{ exists = true }]
  })
}

# ============================================================
# ERROR ALERTING
# ============================================================

resource "aws_sns_topic" "enrichment_error_alerts" {
  name         = "enrichment-error-topic"
  display_name = "Enrichment Error"
}

resource "aws_sns_topic_subscription" "enrichment_error_alert_email_subscriptions" {
  count     = length(local.error_alert_emails_list)
  topic_arn = aws_sns_topic.enrichment_error_alerts.arn
  protocol  = "email"
  endpoint  = local.error_alert_emails_list[count.index]
}
