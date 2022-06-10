output "vpc_id" {
  value = module.network.vpc_id
}

output "database_subnet_group_name" {
  value = module.network.database_subnet_group_name
}