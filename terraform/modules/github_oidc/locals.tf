locals {
  name                        = var.name
  environment                 = var.environment
  github_oidc_create_provider = var.github_oidc_create_provider
  github_oidc_host            = var.github_oidc_host
  github_repo                 = var.github_repo
  github_oidc_provider        = local.github_oidc_create_provider ? aws_iam_openid_connect_provider.github[0] : data.aws_iam_openid_connect_provider.github[0]
}
