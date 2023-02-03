data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "vcite_kms_policy" {
  statement {
    sid = "AllowVCiteRole"

    effect = "Allow"

    principals {
      identifiers = [
        "arn:aws:iam::926041203935:role/vlex-vcite",
      ]
      type = "AWS"
    }

    actions = [
      "kms:*",
    ]
    resources = ["*"]
  }
  statement {
    sid = "EnableLocalAndIAMUserPermissions"

    effect = "Allow"

    principals {
      identifiers = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/tna-s3-tna-${var.environment}-xml-validate",
      ]
      type = "AWS"
    }

    actions = [
      "kms:*",
    ]
    resources = ["*"]
  }
}
