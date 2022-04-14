
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # version = "3.26.0"
      version = ">= 3.69.0, <= 4.4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.0.1"
    }
    # docker = {
    #   # source = "kreuzwerker/docker"
    #   source = "hashicorp/docker"
    #   # version = ">= 0.13"
    # }
  }
  required_version = ">= 1.1.0"

  cloud {
    organization = "mdrx-tna"

    workspaces {
      # name = "tna-dev"
      name = "tna-staging"
    }
  }
}

# data "terraform_remote_state" "vpc" {
#   backend = "remote"

#   config = {
#     organization = "mdr-mdrxtech"
#     workspaces = {
#       name = "mdr-mdrxtech-network-development"
#     }
#   }
# }

module "network" {
  source = "./modules/network"

  # environment                  = "production"
  environment                  = "staging"
  # aws_profile                  = var.aws_profile
  # aws_region                   = var.aws_region
}


module "data" {
  source = "./modules/data"
  environment = "production"
  # name = "development"
  # environment = "ucl"
  # environment = "${var.app_env}"
  # source_bucket = "${var.app_env}-judgement-text-content-bucket"
  # dest_bucket = "${var.app_env}-judgement-xml-enriched-bucket"

  # environment                = "production"
  # aws_profile                = var.aws_profile
  # aws_region                 = var.aws_region

  # vpc_id                     = data.terraform_remote_state.vpc.outputs.vpc_id
  # database_subnet_group_name = data.terraform_remote_state.vpc.outputs.database_subnet_group_name

  vpc_id                     = module.network.vpc_id
  database_subnet_group_name = module.network.database_subnet_group_name
}
# Database
# module "rds-aurora" {
#   source  = "terraform-aws-modules/rds-aurora/aws"
#   version = "6.1.4"
# }

# resource "aws_ssm_parameter" "SSMDatabaseMasterPassword" {
#   name  = "database-master-password"
#   type  = "SecureString"
#   value = random_password.DatabaseMasterPassword.result
# }

# resource "random_password" "DatabaseMasterPassword" {
#   length           = 24
#   special          = true
#   override_special = "!#$%^*()-=+_?{}|"
# }

# resource "aws_rds_cluster" "default" {
#   cluster_identifier      = "aurora-cluster-demo"
#   engine                  = "aurora-mysql"  
#   engine_mode             = "serverless"  
#   database_name           = "myauroradb"  
#   enable_http_endpoint    = true  
#   master_username         = "root"
#   master_password         = "chang333eme321"
#   backup_retention_period = 1
  
#   skip_final_snapshot     = true
  
#   scaling_configuration {
#     auto_pause               = true
#     min_capacity             = 1    
#     max_capacity             = 2
#     seconds_until_auto_pause = 300
#     timeout_action           = "ForceApplyCapacityChange"
#   }  
# }

# locals {
#   name   = "example-${replace(basename(path.cwd), "_", "-")}"
#   region = "eu-west-1"
#   tags = {
#     Owner       = "user"
#     Environment = "dev"
#   }
# }

# ################################################################################
# # Supporting Resources
# ################################################################################

# module "vpc" {
#   source  = "terraform-aws-modules/vpc/aws"
#   version = "~> 3.0"

#   name = local.name
#   cidr = "10.99.0.0/18"

#   azs              = ["${local.region}a", "${local.region}b", "${local.region}c"]
#   public_subnets   = ["10.99.0.0/24", "10.99.1.0/24", "10.99.2.0/24"]
#   private_subnets  = ["10.99.3.0/24", "10.99.4.0/24", "10.99.5.0/24"]
#   database_subnets = ["10.99.7.0/24", "10.99.8.0/24", "10.99.9.0/24"]

#   tags = local.tags
# }

# ################################################################################
# # RDS Aurora Module - PostgreSQL
# ################################################################################

# module "aurora_postgresql" {
#   source = "../../"

#   name              = "${local.name}-postgresql"
#   engine            = "aurora-postgresql"
#   engine_mode       = "serverless"
#   storage_encrypted = true

#   vpc_id                = module.vpc.vpc_id
#   subnets               = module.vpc.database_subnets
#   create_security_group = true
#   allowed_cidr_blocks   = module.vpc.private_subnets_cidr_blocks

#   monitoring_interval = 60

#   apply_immediately   = true
#   skip_final_snapshot = true

#   db_parameter_group_name         = aws_db_parameter_group.example_postgresql.id
#   db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.example_postgresql.id
#   # enabled_cloudwatch_logs_exports = # NOT SUPPORTED

#   scaling_configuration = {
#     auto_pause               = true
#     min_capacity             = 2
#     max_capacity             = 16
#     seconds_until_auto_pause = 300
#     timeout_action           = "ForceApplyCapacityChange"
#   }
# }

# resource "aws_db_parameter_group" "example_postgresql" {
#   name        = "${local.name}-aurora-db-postgres-parameter-group"
#   family      = "aurora-postgresql10"
#   description = "${local.name}-aurora-db-postgres-parameter-group"
#   tags        = local.tags
# }

# resource "aws_rds_cluster_parameter_group" "example_postgresql" {
#   name        = "${local.name}-aurora-postgres-cluster-parameter-group"
#   family      = "aurora-postgresql10"
#   description = "${local.name}-aurora-postgres-cluster-parameter-group"
#   tags        = local.tags
# }