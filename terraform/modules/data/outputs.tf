output "postgress_master_password" {
  value = aws_secretsmanager_secret_version.postgress_master_password.secret_id
}

output "postgress_hostname" {
  value = module.metadata-db.rds_cluster_endpoint
}

output "aws_vpc" {
  value = data.aws_vpc.vpc.id
}

output "aws_subnets_private_ids" {
  value = toset(data.aws_subnets.private.ids)
}

output "rds_security_group_id" {
  value = module.metadata-db.security_group_id
}
