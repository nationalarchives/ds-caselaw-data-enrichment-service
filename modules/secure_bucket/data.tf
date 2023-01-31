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
}
