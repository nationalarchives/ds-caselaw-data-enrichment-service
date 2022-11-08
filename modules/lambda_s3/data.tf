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
