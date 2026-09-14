module "aurora-metadata-db" {
  for_each = local.aurora_rds

  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "10.4.0"

  name = "${local.name}-${each.key}-metadata-db-${local.environment}"

  engine          = "aurora-postgresql"
  engine_version  = each.value["engine_version"]
  master_username = "root"

  manage_master_user_password = false
  master_password_wo          = aws_secretsmanager_secret_version.aurora_postgress_master_password[each.key].secret_string
  master_password_wo_version  = each.value["password_version"]

  vpc_id                = var.vpc_id
  db_subnet_group_name  = var.database_subnet_group_name
  create_security_group = true
  security_group_ingress_rules = {
    for index, security_group_id in each.value["allowed_security_groups"] :
    "allowed_security_group_${index}" => {
      referenced_security_group_id = security_group_id
    }
  }

  deletion_protection = local.db[local.environment].deletion_protection

  apply_immediately   = true
  skip_final_snapshot = true

  cluster_parameter_group_name    = aws_rds_cluster_parameter_group.aurora_postgres[each.key].id
  enabled_cloudwatch_logs_exports = ["postgresql"]

  database_name = "rules"
  instances = {
    one = {
      ca_cert_identifier      = "rds-ca-rsa4096-g1"
      db_parameter_group_name = aws_db_parameter_group.aurora_postgres[each.key].id
      instance_class          = each.value["instance_type"]
    }
  }

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
