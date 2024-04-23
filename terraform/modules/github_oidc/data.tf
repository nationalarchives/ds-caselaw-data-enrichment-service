data "external" "github_oidc_certificate_thumbprint" {
  program = ["/bin/bash", "${path.module}/external-data-scripts/get-certificate-thumbprint.sh"]

  query = {
    host = local.github_oidc_host
  }
}
