output "aurora_postgress_master_password" {
  value = { for k, v in local.aurora_rds : k => aws_secretsmanager_secret_version.aurora_postgress_master_password[k].secret_id }
}

output "aurora_postgress_hostname" {
  value = { for k, v in local.aurora_rds : k => module.aurora-metadata-db[k].rds_cluster_endpoint }
}

output "aws_vpc" {
  value = data.aws_vpc.vpc.id
}

output "aws_subnets_private_ids" {
  value = toset(data.aws_subnets.private.ids)
}

output "aurora_security_group_ids" {
  value = [for k, v in local.aurora_rds : module.aurora-metadata-db[k].security_group_id]
}
