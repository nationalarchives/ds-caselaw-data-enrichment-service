# module "dest_bucket" {
#   source = "../secure_bucket"

#   bucket_name = "${local.environment}-${local.name}-dest-bucket"
# #   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

#   tags = local.tags

# }

# module "source_bucket" {
#   source = "../secure_bucket"

#   bucket_name = "${local.environment}-${local.name}-source-bucket"
# #   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

#   tags = local.tags
# }

module "xml_original_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-xml-original-bucket"
#   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

  tags = local.tags
}

module "text_content_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-text-content-bucket"
#   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

  tags = local.tags
}

module "xml_enriched_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-xml-enriched-bucket"
#   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

  tags = local.tags
}

module "replacements_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-replacements-bucket"
#   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

  tags = local.tags
}

module "rules_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-rules-bucket"
#   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

  tags = local.tags
}

module "container_bucket" {
  source = "../secure_bucket"

  bucket_name = "${local.environment}-${local.name}-container-bucket"
#   policy_json = data.aws_iam_policy_document.dest_bucket_policy.json

  tags = local.tags
}

# setup notifications
# resource "aws_s3_bucket_notification" "xml_enriched_bucket_notification" {
#   bucket = module.xml_enriched_bucket.id

#   queue {
#     queue_arn     = aws_sqs_queue.validation-queue.arn
#     events        = ["s3:ObjectCreated:*"]
#     filter_suffix = ".log"
#   }
# }

# # SQS queue
# resource "xml_original_bucket_sqs_queue" "queue" {
#   name = "${local.environment}-${local.name}-xml_original_bucket-event-notification-queue"

#   policy = <<POLICY
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Principal": "*",
#       "Action": "sqs:SendMessage",
#       "Resource": "arn:aws:sqs:*:*:${this.name}",
#       "Condition": {
#         "ArnEquals": { "aws:SourceArn": "${xml_original_bucket.bucket.arn}" }
#       }
#     }
#   ]
# }
# POLICY
# }