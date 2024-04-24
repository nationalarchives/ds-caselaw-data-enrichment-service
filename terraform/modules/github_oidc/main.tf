resource "aws_iam_openid_connect_provider" "github" {
  count = local.github_oidc_create_provider ? 1 : 0

  url             = "https://${local.github_oidc_host}"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.external.github_oidc_certificate_thumbprint[0].result.thumbprint]
}

data "aws_iam_policy_document" "github_oidc_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "${local.github_oidc_host}:sub"
      values   = ["repo:${local.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_oidc" {
  name               = "${local.name}-${local.environment}-github-oidc"
  description        = "${local.name} ${local.environment} GitHub OIDC"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "github_oidc_administrator_access" {
  role       = aws_iam_role.github_oidc.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
