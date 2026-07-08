locals {
  name         = "tna-s3-${var.name}"
  region       = var.aws_region
  environment  = var.environment
  api_endpoint = var.api_endpoint
  tags = {
    Environment = var.environment
    Project     = "TNA-enrichment"
  }
}
