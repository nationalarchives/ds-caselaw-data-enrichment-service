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

  tags = {
    Environment = var.environment
    Project     = "TNA judgement enrichment"
  }
}
