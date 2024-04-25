data "aws_iam_policy_document" "jump_host_assume_role" {
  version = "2012-10-17"

  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "ec2.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role" "jump_host" {
  name               = "${local.name}-${local.environment}-jump-host"
  description        = "${local.name} ${local.environment} jump-host"
  assume_role_policy = data.aws_iam_policy_document.jump_host_assume_role.json
}

data "aws_iam_policy_document" "jump_host_ssm_dhmc" {
  version = "2012-10-17"

  statement {
    effect = "Allow"
    actions = [
      "iam:PassRole"
    ]
    resources = [
      "arn:aws:iam::${local.aws_account_id}:role/${data.external.ssm_dhmc_setting.result.setting_value}"
    ]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values = [
        "ssm.amazonaws.com"
      ]
    }
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetServiceSetting",
      "ssm:ResetServiceSetting",
      "ssm:UpdateServiceSetting"
    ]
    resources = [
      "arn:aws:iam::${local.aws_account_id}:role/${data.external.ssm_dhmc_setting.result.setting_value}"
    ]
  }
}

resource "aws_iam_policy" "jump_host_ssm_dhmc" {
  name   = "${local.name}-${local.environment}-jump-host-ssm-dhmc"
  policy = data.aws_iam_policy_document.jump_host_ssm_dhmc.json
}

resource "aws_iam_role_policy_attachment" "jump_host_ssm_dhmc" {
  role       = aws_iam_role.jump_host.name
  policy_arn = aws_iam_policy.jump_host_ssm_dhmc.arn
}

resource "aws_iam_instance_profile" "jump_host" {
  name = "${local.name}-${local.environment}-jump-host"
  role = aws_iam_role.jump_host.name

  depends_on = [
    aws_iam_role_policy_attachment.jump_host_ssm_dhmc,
  ]
}
