variable "aws_profile" {
  type    = string
  default = "default"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
  # default = "eu-west-1" #for testing
}

variable "vpc_id" {
  type = string
}

variable "environment" {
  type = string
  # default = "ucl"
  default = "development"
}

variable "database_subnet_group_name" {
  type = string
}