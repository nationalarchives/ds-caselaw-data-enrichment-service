module "aurora-metadata-db" {
  for_each = local.aurora_rds

  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "9.11.0"

  name = "${local.name}-${each.key}-metadata-db-${local.environment}"

  engine             = "aurora-postgresql"
  engine_version     = each.value["engine_version"]
  instance_type      = each.value["instance_type"]
  ca_cert_identifier = "rds-ca-rsa4096-g1"

  vpc_id                  = var.vpc_id
  subnets                 = data.aws_subnets.database.ids
  create_security_group   = true
  allowed_security_groups = each.value["allowed_security_groups"]

  deletion_protection = local.db[local.environment].deletion_protection

  password = aws_secretsmanager_secret_version.aurora_postgress_master_password[each.key].secret_string

  apply_immediately   = true
  skip_final_snapshot = true

  db_parameter_group_name         = aws_db_parameter_group.aurora_postgres[each.key].id
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.aurora_postgres[each.key].id
  enabled_cloudwatch_logs_exports = ["postgresql"]

  database_name = "rules"

  depends_on = [
    aws_db_parameter_group.aurora_postgres,
    aws_rds_cluster_parameter_group.aurora_postgres,
    aws_secretsmanager_secret_version.aurora_postgress_master_password,
  ]

  tags = local.tags
}

resource "aws_db_parameter_group" "aurora_postgres" {
  for_each = local.aurora_rds

  name        = "${local.name}-${each.key}-aurora-db-postgres${split(".", each.value["engine_version"])[0]}-parameter-group"
  family      = "aurora-postgresql${split(".", each.value["engine_version"])[0]}"
  description = "${local.name}-${each.key}-aurora-db-postgres${split(".", each.value["engine_version"])[0]}-parameter-group"
  tags        = local.tags
}

resource "aws_rds_cluster_parameter_group" "aurora_postgres" {
  for_each = local.aurora_rds

  name        = "${local.name}-${each.key}-aurora-postgres${split(".", each.value["engine_version"])[0]}-cluster-parameter-group"
  family      = "aurora-postgresql${split(".", each.value["engine_version"])[0]}"
  description = "${local.name}-${each.key}-aurora-postgres${split(".", each.value["engine_version"])[0]}-cluster-parameter-group"
  tags        = local.tags
}
