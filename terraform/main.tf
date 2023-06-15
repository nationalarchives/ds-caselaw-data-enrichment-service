
terraform {
  required_version = ">=1.4"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=5.3.0,<6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.1, <= 4.0"
    }
  }

  backend "s3" {
    # bucket = "${var.backend_bucket}"
    key    = "ds-infrastructure-enrichment-pipeline/backend.tfstate"
    region = "eu-west-2"
  }


}

module "lambda_s3" {
  source = "./modules/lambda_s3"
  name   = "tna"

  environment = var.app_env

  bucket_prefix = "sg"

  vpc_id = module.network.vpc_id

  postgress_master_password_secret_id = module.data.postgress_master_password
  postgress_hostname                  = module.data.postgress_hostname

  # sparql_username = "${module.data.sparql_username}"
  # sparql_password = "${module.data.sparql_password}"

  default_security_group_id = module.network.default_security_group_id

  aws_subnets_private_ids = module.data.aws_subnets_private_ids
}

module "network" {
  source = "./modules/network"

  environment = var.app_env
}


module "data" {
  source = "./modules/data"

  environment = var.app_env

  vpc_id                     = module.network.vpc_id
  database_subnet_group_name = module.network.database_subnet_group_name
}
