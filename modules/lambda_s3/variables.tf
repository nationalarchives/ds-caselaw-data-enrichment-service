variable "aws_profile" {
  type    = string
  default = "default"
  # default = var.aws_profile
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
  # default = "eu-west-1"
  # default = var.aws_region
}

variable "name" {
  type = string
}

variable "environment" {
  type = string
}

# variable "source_bucket" {
#   type = string
# }

# variable "dest_bucket" {
#   type = string
# }

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
  default = "python3.8"
}

variable "lambda_source_path" {
  type    = string
  default = "src/lambdas/"
}

variable "postgress_master_password_secret_id" {
  type = string
  # default = "arn:aws:secretsmanager:eu-west-1:849689169827:secret:tna-postgress-password-ucldetf-tk6tPh"
}

variable "postgress_hostname" {
  type = string
  # default = "tna-metadata-db-ucldetf-1.cvbrurw4plvi.eu-west-1.rds.amazonaws.com"
}

# variable "sparql_username" {
#   type    = string
# }

# variable "sparql_password" {
#   type    = string
# }

variable "vpc_id" {
  type = string
}

variable "default_security_group_id" {
  type = string
}
# variable "public_subnets" {
#   type    = list
# }

variable "aws_subnets_private_ids" {
  type = list(any)
}

variable "bucket_prefix" {
  default = "sg"
}
