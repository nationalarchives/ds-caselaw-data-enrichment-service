terraform {
  required_version = ">=1.4"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.3.0, < 6.0.0"
    }
  }

}

module "network" {
  source = "../modules/network"

  environment = "production"
  aws_profile = var.aws_profile
  aws_region  = var.aws_region
}
