output "kms_key_id" {
  value = var.use_kms_encryption ? aws_kms_key.this[0].id : null
}

output "kms_key_arn" {
  value = var.use_kms_encryption ? aws_kms_key.this[0].arn : null
}

output "s3_bucket_arn" {
  value = module.this.s3_bucket_arn
}

output "s3_bucket_id" {
  value = module.this.s3_bucket_id
}
