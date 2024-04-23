locals {
  name        = "tna-network"
  region      = var.aws_region
  environment = var.environment

  environment_cidr_blocks = {
    "dev"        = 0
    "staging"    = 1
    "production" = 2
  }

  public_cidr_blocks   = [cidrsubnet(var.vpc_cidr_block, 4, 2), cidrsubnet(var.vpc_cidr_block, 4, 3)]
  database_cidr_blocks = [cidrsubnet(var.vpc_cidr_block, 4, 4), cidrsubnet(var.vpc_cidr_block, 4, 5)]
  private_cidr_blocks  = [cidrsubnet(var.vpc_cidr_block, 4, 6), cidrsubnet(var.vpc_cidr_block, 4, 7)]

  vpc = {
    staging = {
      single_ngw = true
    }
    production = {
      single_ngw = false
    }
  }

  tags = {
    Environment = var.environment
    Project     = "tna"
  }
}
