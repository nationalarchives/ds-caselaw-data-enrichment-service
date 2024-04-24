data "aws_caller_identity" "current" {}

data "external" "github_oidc_certificate_thumbprint" {
  count = local.github_oidc_create_provider ? 1 : 0

  program = ["/bin/bash", "${path.module}/external-data-scripts/get-certificate-thumbprint.sh"]

  query = {
    host = local.github_oidc_host
  }
}

data "aws_iam_openid_connect_provider" "github" {
  count = local.github_oidc_create_provider ? 0 : 1

  arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.github_oidc_host}"
}
