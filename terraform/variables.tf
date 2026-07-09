variable "region" {
  default     = "eu-west-2"
  description = "AWS Region to deploy to"
}

variable "app_env" {
  default     = "staging"
  description = "Common prefix for all Terraform created resources"
}

variable "bucket_prefix" {
  default = "sg"
}

variable "vcite_enabled" {
  type        = bool
  description = "Enable vCite processing and upload in enrichment lambda"
}

variable "api_endpoint" {
  type        = string
  description = "Base API endpoint used by enrichment lambda"
}

variable "api_username" {
  type        = string
  description = "API username to store in AWS Secrets Manager"
  sensitive   = true
}

variable "api_password" {
  type        = string
  description = "API password to store in AWS Secrets Manager"
  sensitive   = true
}

variable "sparql_username" {
  type        = string
  description = "SPARQL username to store in AWS Secrets Manager"
  sensitive   = true
}

variable "sparql_password" {
  type        = string
  description = "SPARQL password to store in AWS Secrets Manager"
  sensitive   = true
}
