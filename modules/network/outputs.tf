output "vpc_id" {
  value = module.vpc.vpc_id
}

output "database_subnet_group_name" {
  value = module.vpc.database_subnet_group
}

output "public_subnets" {
  # value = "${element(tolist(module.vpc.public_subnets.ids))}"
  # value = "${tolist(module.vpc.public_subnets.ids)}"
  # for_each = module.vpc.public_subnets.ids
  # value =each.value
  # value = "${module.vpc.public_subnets.ids}"
  value = []
}

output "default_security_group_id" {
  value = module.vpc.default_security_group_id
}
