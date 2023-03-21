variable "aws_profile" {
  type    = string
  default = "default"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
  # default = "eu-west-1"
}

variable "environment" {
  type = string
}

variable "vpc_cidr_block" {
  type    = string
  default = "172.19.0.0/16"
}
