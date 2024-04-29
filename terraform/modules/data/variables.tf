variable "aws_profile" {
  type    = string
  default = "default"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "vpc_id" {
  type = string
}

variable "default_security_group_ids" {
  type = list(string)
}

variable "environment" {
  type    = string
  default = "development"
}

variable "database_subnet_group_name" {
  type = string
}
