locals {
  name           = var.name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = data.aws_region.current.name
  subnet_id      = var.subnet_id
  instance_type  = var.instance_type
}
