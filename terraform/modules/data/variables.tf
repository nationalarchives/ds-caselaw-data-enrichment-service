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

variable "environment" {
  type    = string
  default = "development"
}

variable "database_subnet_group_name" {
  type = string
}

variable "aurora_rds" {
  type = map(object({
    engine_version          = string
    instance_type           = string
    allowed_security_groups = list(string)
  }))
}
