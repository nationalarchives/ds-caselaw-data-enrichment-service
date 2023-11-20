variable "error_alert_emails" {
  type    = string
  default = "[]"
}

locals {
  error_alert_emails_list = jsondecode(var.error_alert_emails)
}

variable "aws_profile" {
  type    = string
  default = "default"
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
variable "source_bucket_folder" {
  type    = string
  default = ""
}

variable "container_image_tag" {
  type    = string
  default = "latest"
}

variable "memory_size" {
  type    = number
  default = 128
}

variable "source_filter_suffix" {
  type    = string
  default = ""
}

variable "use_container_image" {
  type    = bool
  default = false
}

variable "lambda_handler" {
  type    = string
  default = ""
}

variable "runtime" {
  type    = string
  default = "python3.10"
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

variable "vpc_id" {
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
