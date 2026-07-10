variable "error_alert_emails" {
  type    = string
  default = "[]"
}

locals {
  error_alert_emails_list = jsondecode(var.error_alert_emails)
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "name" {
  type = string
}

variable "environment" {
  type = string
}

variable "api_endpoint" {
  type = string
}

variable "container_image_tag" {
  type    = string
  default = "latest"
}

variable "lambda_source_path" {
  type    = string
  default = "../src/lambdas/"
}

variable "postgress_master_password_secret_id" {
  type = string
}

variable "postgress_hostname" {
  type = string
}

variable "default_security_group_id" {
  type = string
}

variable "aws_subnets_private_ids" {
  type = list(any)
}

variable "bucket_prefix" {
  default = "sg"
}

variable "vcite_enabled" {
  type = bool
}

variable "api_username" {
  type      = string
  sensitive = true
}

variable "api_password" {
  type      = string
  sensitive = true
}

variable "sparql_username" {
  type      = string
  sensitive = true
}

variable "sparql_password" {
  type      = string
  sensitive = true
}
