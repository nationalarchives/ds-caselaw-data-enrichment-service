terraform {
  required_version = ">=1.4"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.3.0, < 6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.1, <= 4.0"
    }
  }

  backend "s3" {
    key    = "ds-infrastructure-enrichment-pipeline/backend.tfstate"
    region = "eu-west-2"
  }
}

module "lambda_s3" {
  source = "./modules/lambda_s3"

  name = "tna"

  environment = var.app_env

  bucket_prefix = "sg"

  vpc_id = module.network.vpc_id

  postgress_master_password_secret_id = module.data.aurora_postgress_master_password["main"]
  postgress_hostname                  = module.data.aurora_postgress_hostname["main"]

  default_security_group_id = module.network.default_security_group_id

  aws_subnets_private_ids = module.data.aws_subnets_private_ids
}

module "network" {
  source = "./modules/network"

  environment = var.app_env

  rds_security_group_ids = module.data.aurora_security_group_ids
}

module "data" {
  source = "./modules/data"

  environment = var.app_env

  vpc_id                     = module.network.vpc_id
  database_subnet_group_name = module.network.database_subnet_group_name

  aurora_rds = {
    "main" = {
      engine_version = "16.2"
      instance_type  = "db.t3.medium"
      allowed_security_groups = [
        module.network.default_security_group_id,
        module.jump_host.security_group_id,
      ]
    }
  }
}

module "github_oidc" {
  source = "./modules/github_oidc"

  name                        = "tna"
  environment                 = var.app_env
  github_repo                 = "nationalarchives/ds-caselaw-data-enrichment-service"
  github_oidc_create_provider = false
}

module "jump_host" {
  source = "./modules/jump_host"

  name          = "tna"
  environment   = var.app_env
  instance_type = "t2.micro"
  subnet_id     = module.network.database_subnet_ids[0]
}
