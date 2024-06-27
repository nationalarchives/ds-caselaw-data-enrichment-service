resource "random_password" "aurora_password" {
  for_each = local.aurora_rds

  length  = 50
  special = true
  # Postgress passwords can't contain any of the following:
  # / (slash), '(single quote), "(double quote) and @ (at sign).
  override_special = "!#$%&*()-_=+[]"
}

resource "aws_secretsmanager_secret" "aurora_postgress_master_password" {
  for_each = local.aurora_rds

  name                    = "${local.name}-${each.key}-postgress-password-${local.environment}"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "aurora_postgress_master_password" {
  for_each = local.aurora_rds

  secret_id     = aws_secretsmanager_secret.aurora_postgress_master_password[each.key].id
  secret_string = random_password.aurora_password[each.key].result
}
