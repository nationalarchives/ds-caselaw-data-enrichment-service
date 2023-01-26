terraform {
  required_version = ">=1.1.0,<1.2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=3.0.0,<4.0.0"
    }
  }
  #   cloud {
  #     organization = "mdr-research"

  #     workspaces {
  #       name = "mdr-insights-network-production"
  #     }
  #   }

}

module "network" {
  source = "../modules/network"

  environment = "production"
  aws_profile = var.aws_profile
  aws_region  = var.aws_region
}