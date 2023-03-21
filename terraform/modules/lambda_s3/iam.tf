# data "aws_iam_policy_document" "dest_bucket_policy" {
#   statement {
#     principals {
#       type = "AWS"
#       identifiers = [
#         module.lambda.lambda_role_arn
#       ]
#     }

#     actions = ["s3:PutObject", "s3:PutObjectAcl"]
#     resources = [
#       "${module.dest_bucket.s3_bucket_arn}/*"
#     ]

#   }

# }

# data "aws_iam_policy_document" "xml_original_bucket_policy" {
#   statement {
#     principals {
#       type = "AWS"
#       identifiers = [
#         module.lambda.lambda_role_arn
#       ]
#     }

#     actions = ["s3:PutObject", "s3:PutObjectAcl"]
#     resources = [
#       "${module.xml_original_bucket.s3_bucket_arn}/*"
#     ]

#   }

# }
