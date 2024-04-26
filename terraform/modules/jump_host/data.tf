data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# aws_ssm_service_setting doesn't yet have a data source, so we need to use
# a script to retrieve SSM service settings
# https://github.com/hashicorp/terraform-provider-aws/issues/25170
data "external" "ssm_dhmc_setting" {
  program = ["/bin/bash", "${path.module}/external-data-scripts/get-ssm-service-setting.sh"]

  query = {
    setting_id = "arn:aws:ssm:${local.aws_region}:${local.aws_account_id}:servicesetting/ssm/managed-instance/default-ec2-instance-management-role"
  }
}

data "aws_ami" "jump_host" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name = "name"
    values = [
      "al2023-ami-2023*"
    ]
  }

  filter {
    name = "architecture"
    values = [
      "x86_64"
    ]
  }
}

data "aws_subnet" "jump_host" {
  id = local.subnet_id
}
