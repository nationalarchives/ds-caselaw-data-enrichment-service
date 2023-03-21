locals {
  name        = "tna-s3-${var.name}"
  region      = var.aws_region
  environment = var.environment
  tags = {
    Environment = var.environment
    Project     = "TNA-enrichment"
  }
}
