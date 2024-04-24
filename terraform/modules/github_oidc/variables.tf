variable "name" {
  description = "Name of project"
  type        = string
}

variable "environment" {
  description = "Environment name. This along with `name` will be prefixed to resource names"
  type        = string
}

variable "github_oidc_create_provider" {
  description = "Conditionally create GitHub OpenID Connect provider. Only 1 provider configured with the GitHub url is allowed. Set to `false` to use the existing one."
  type        = bool
}

variable "github_oidc_host" {
  description = "GitHub OpenID host name"
  type        = string
  default     = "token.actions.githubusercontent.com"
}

variable "github_repo" {
  description = "The name of the repository (username/repo) to allow GitHub actions to run actions against the AWS account"
  type        = string
}
