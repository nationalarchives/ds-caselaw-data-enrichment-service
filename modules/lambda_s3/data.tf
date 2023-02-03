data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "sqs_policy_fetch_xml" {
  statement {
    sid    = "ReceiveActions"
    effect = "Allow"
    actions = [
      "sqs:*"
    ]
    principals {
      identifiers = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
      type = "AWS"
    }
  }
  statement {
    sid       = "SenderActions"
    effect    = "Allow"
    resources = [aws_sqs_queue.fetch_xml_queue.arn]
    actions = [
      "sqs:*",
    ]
    principals {
      identifiers = [
        "sns.amazonaws.com"
      ]
      type = "Service"
    }
    condition {
      test = "StringEquals"
      values = [
        "arn:aws:sns:eu-west-2:626206937213:caselaw-stg-judgment-updated",
        "arn:aws:sns:eu-west-2:276505630421:caselaw-judgment-updated",
      ]
      variable = "aws:SourceArn"
    }
  }
}

data "aws_iam_policy_document" "vcite_policy" {
  statement {
    sid    = "Access"
    effect = "Allow"

    principals {
      identifiers = [
        "arn:aws:iam::926041203935:role/vlex-vcite",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/tna-s3-tna-${local.environment}-xml-validate",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/tna-s3-tna-${local.environment}-push-enriched-xml"
      ]
      type = "AWS"
    }

    actions = [
      "s3:List*",
      "s3:ListBucket",
      "s3:Get*",
      "s3:Put*",
    ]

    resources = [
      "${module.vcite_enriched_bucket.s3_bucket_arn}",
      "${module.vcite_enriched_bucket.s3_bucket_arn}/*",
    ]
  }
}

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
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/tna-s3-tna-${local.environment}-push-enriched-xml",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/tna-s3-tna-${local.environment}-xml-validate",
      ]
      type = "AWS"
    }

    actions = [
      "kms:*",
    ]
    resources = ["*"]
  }
}

