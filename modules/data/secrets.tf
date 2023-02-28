resource "random_password" "password" {
  length  = 50
  special = true
  # override_special = "_%@"
  # override_special = "'/@\"_% "
  # Postgress passwords can't contain any of the following:
  # / (slash), '(single quote), "(double quote) and @ (at sign).
  override_special = "!#$%&*()-_=+[]"
}

resource "aws_secretsmanager_secret" "postgress_master_password" {
  name                    = "${local.name}-postgress-password-${local.environment}"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "postgress_master_password" {
  secret_id     = aws_secretsmanager_secret.postgress_master_password.id
  secret_string = random_password.password.result
}

# resource "aws_secretsmanager_secret" "sparql_username" {
#   name                    = "${local.name}-sparql-username-${local.environment}"
#   recovery_window_in_days = 0
# }

# resource "aws_secretsmanager_secret_version" "sparql_username" {
#   secret_id     = aws_secretsmanager_secret.sparql_username.id
#   secret_string = ""
# }

# resource "aws_secretsmanager_secret" "sparql_password" {
#   name                    = "${local.name}-sparql-password-${local.environment}"
#   recovery_window_in_days = 0
# }

# resource "aws_secretsmanager_secret_version" "sparql_password" {
#   secret_id     = aws_secretsmanager_secret.sparql_password.id
#   secret_string = ""
# }

# resource "random_password" "app_secret" {
#   length      = 32
#   special     = true
#   upper       = true
#   lower       = true
#   min_upper   = 3
#   min_special = 2
#   min_numeric = 3
#   min_lower   = 3
# }

# module "secrets" {
#   source      = "../secrets"
#   name        = local.name
#   environment = local.environment
#   application-secrets = {
#     "SECRET_KEY"              = random_password.app_secret.result
#     "SQLALCHEMY_DATABASE_URI" = "postgres://${module.metadata-db.rds_cluster_master_username}:${module.metadata-db.rds_cluster_master_password}@${module.metadata-db.rds_cluster_endpoint}:${module.metadata-db.rds_cluster_port}/${module.metadata-db.rds_cluster_database_name}"
#   }
# }
