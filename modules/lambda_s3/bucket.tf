
module "xml_original_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-xml-original-bucket"

  tags = local.tags
}

module "test-bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-test-bucket"

  tags = local.tags
}

module "text_content_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-text-content-bucket"

  tags = local.tags
}

module "xml_enriched_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-xml-enriched-bucket"

  tags = local.tags
}

module "xml_second_phase_enriched_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-xml-second-phase-enriched-bucket"

  tags = local.tags
}

module "xml_third_phase_enriched_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-xml-third-phase-enriched-bucket"

  tags = local.tags
}

module "replacements_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-replacements-bucket"

  tags = local.tags
}

module "rules_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-rules-bucket"

  tags = local.tags
}

module "tracking_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-enrichment-tracking"

  tags = local.tags
}

module "container_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-container-bucket"

  tags = local.tags
}

module "vcite_enriched_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-vcite-enriched-bucket"

  policy_json = data.aws_iam_policy_document.vcite_policy.json

  tags = local.tags
}

module "db_backup" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-${var.bucket_prefix}-db-backups"
}
