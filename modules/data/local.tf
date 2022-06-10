locals {
  name        = "tna"
  region      = var.aws_region
  environment = var.environment
  tags = {
    Environment = var.environment
    Project     = "TNA judgement enrichment"
  }
}