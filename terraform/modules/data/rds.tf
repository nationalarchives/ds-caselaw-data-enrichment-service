module "metadata-db" {
  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "5.3.0"

  name = "${local.name}-metadata-db-${local.environment}"

  engine         = "aurora-postgresql"
  engine_version = "11.17"
  instance_type  = "db.t3.medium"

  vpc_id                  = var.vpc_id
  subnets                 = data.aws_subnets.database.ids
  create_security_group   = true
  allowed_security_groups = var.default_security_group_ids

  deletion_protection = local.db[local.environment].deletion_protection

  password = aws_secretsmanager_secret_version.postgress_master_password.secret_string

  apply_immediately   = true
  skip_final_snapshot = true

  db_parameter_group_name         = aws_db_parameter_group.example.id
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.example.id
  enabled_cloudwatch_logs_exports = ["postgresql"]

  database_name = "rules"

  tags = local.tags
}

resource "aws_db_parameter_group" "example" {
  name        = "${local.name}-aurora-db-postgres11-parameter-group"
  family      = "aurora-postgresql11"
  description = "${local.name}-aurora-db-postgres11-parameter-group"
  tags        = local.tags
}

resource "aws_rds_cluster_parameter_group" "example" {
  name        = "${local.name}-aurora-postgres11-cluster-parameter-group"
  family      = "aurora-postgresql11"
  description = "${local.name}-aurora-postgres11-cluster-parameter-group"
  tags        = local.tags
}
