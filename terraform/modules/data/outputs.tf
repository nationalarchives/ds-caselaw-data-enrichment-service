
output "postgress_master_password" {
  #   value = aws_secretsmanager_secret.postgress_master_password.secret_id
  value = aws_secretsmanager_secret_version.postgress_master_password.secret_id
}

output "postgress_hostname" {
  value = module.metadata-db.rds_cluster_endpoint
}

# output "sparql_username" {
#   value = aws_secretsmanager_secret.sparql_username
# }

# output "sparql_password" {
#   value = aws_secretsmanager_secret.sparql_password
# }

output "aws_vpc" {
  value = data.aws_vpc.vpc.id
}

# public_subnets = "${module.network.public_subnets}"
# for_each = toset(module.data.data.aws_subnets.private.ids)
# id       = each.value
# subnet_ids = [each.value]
output "aws_subnets_private_ids" {
  # for_each = toset(data.aws_subnets.private.ids)
  # value = [each.value]
  # value = data.aws_subnet.private[each.key]
  value = toset(data.aws_subnets.private.ids)
}

output "rds_security_group_id" {
  value = module.metadata-db.security_group_id
}
