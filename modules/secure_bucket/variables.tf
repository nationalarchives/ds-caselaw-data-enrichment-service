variable "bucket_name" {
  type = string
}

variable "policy_json" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "use_kms_encryption" {
  type    = bool
  default = true
}
