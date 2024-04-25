variable "name" {
  description = "Name of project"
  type        = string
}

variable "environment" {
  description = "Environment name. This along with `name` will be prefixed to resource names"
  type        = string
}

variable "subnet_id" {
  description = "subnet id in which to launch the jump host"
  type        = string
}

variable "instance_type" {
  description = "Instance type of the EC2 instance"
  type        = string
}
