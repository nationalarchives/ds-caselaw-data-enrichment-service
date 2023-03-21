resource "aws_kms_key" "this" {
  count = var.use_kms_encryption ? 1 : 0

  description             = "KMS key used to encrypt bucket ${var.bucket_name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy                  = var.vcite_enriched ? var.kms_policy_json : null #data.aws_iam_policy_document.vcite_kms_policy.json : null
}

resource "aws_kms_alias" "this" {
  count = var.use_kms_encryption ? 1 : 0

  name          = "alias/${var.bucket_name}-kms-key"
  target_key_id = aws_kms_key.this[0].key_id
}
