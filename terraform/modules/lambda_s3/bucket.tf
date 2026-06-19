# rules_bucket - holds citation_patterns.jsonl; read by enrichment lambda and update_rules_processor
module "rules_bucket" {
  source      = "../secure_bucket"
  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-rules-bucket"
  tags        = local.tags
}

# Notification: update_rules_processor triggered when new rules are uploaded
resource "aws_s3_bucket_notification" "rules_bucket_notification" {
  bucket = module.rules_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-update-rules-processor.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".jsonl"
  }
}

# container_bucket - deployment artefacts
module "container_bucket" {
  source      = "../secure_bucket"
  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-container-bucket"
  tags        = local.tags
}

# vcite_enriched_bucket - output for vlex integration
module "vcite_enriched_bucket" {
  source          = "../secure_bucket"
  bucket_name     = "${local.environment}-${local.name}-${var.bucket_prefix}-vcite-enriched-bucket"
  policy_json     = data.aws_iam_policy_document.vcite_policy.json
  kms_policy_json = data.aws_iam_policy_document.vcite_kms_policy.json
  vcite_enriched  = true
  tags            = local.tags
}

# Notification: when vCite writes back enriched XML, route callback to enrichment lambda
resource "aws_s3_bucket_notification" "vcite_enriched_bucket_notification" {
  bucket = module.vcite_enriched_bucket.s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda-enrichment.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".xml"
  }
}
