module "this" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.6.1"

  bucket = var.bucket_name

  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
  ignore_public_acls      = true

  attach_policy                         = var.policy_json != null ? true : false
  policy                                = var.policy_json
  attach_deny_insecure_transport_policy = var.policy_json != null ? true : false

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        kms_master_key_id = var.use_kms_encryption ? aws_kms_key.this[0].arn : null
        sse_algorithm     = var.use_kms_encryption ? "aws:kms" : "AES256"
      }

      bucket_key_enabled = var.use_kms_encryption
    }

  }

  versioning = {
    enabled = true
  }

  lifecycle_rule = [
    {
      id                                     = "delete-incomplete-mpu"
      enabled                                = true
      prefix                                 = ""
      abort_incomplete_multipart_upload_days = 1
    }
  ]

  tags = var.tags
}
