output "vpc_id" {
  value = module.vpc.vpc_id
}

output "database_subnet_group_name" {
  value = module.vpc.database_subnet_group
}

output "public_subnets" {
  value = []
}

output "default_security_group_id" {
  value = module.vpc.default_security_group_id
}
