<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.4 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >=5.3.0,<6.0.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | >= 3.5.1, <= 4.0 |

## Providers

No providers.

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_data"></a> [data](#module\_data) | ./modules/data | n/a |
| <a name="module_github_oidc"></a> [github\_oidc](#module\_github\_oidc) | ./modules/github_oidc | n/a |
| <a name="module_lambda_s3"></a> [lambda\_s3](#module\_lambda\_s3) | ./modules/lambda_s3 | n/a |
| <a name="module_network"></a> [network](#module\_network) | ./modules/network | n/a |

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_app_env"></a> [app\_env](#input\_app\_env) | Common prefix for all Terraform created resources | `string` | `"staging"` | no |
| <a name="input_bucket_prefix"></a> [bucket\_prefix](#input\_bucket\_prefix) | n/a | `string` | `"sg"` | no |
| <a name="input_region"></a> [region](#input\_region) | AWS Region to deploy to | `string` | `"eu-west-2"` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
