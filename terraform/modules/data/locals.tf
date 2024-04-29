locals {
  name        = "tna"
  region      = var.aws_region
  environment = var.environment

  db = {
    staging = {
      deletion_protection = true
    }
    production = {
      deletion_protection = true
    }
  }

  aurora_rds = var.aurora_rds

  tags = {
    Environment = var.environment
    Project     = "TNA judgement enrichment"
  }
}
