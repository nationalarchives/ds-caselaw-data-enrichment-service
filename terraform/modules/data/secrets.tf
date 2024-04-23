resource "random_password" "password" {
  length  = 50
  special = true
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
