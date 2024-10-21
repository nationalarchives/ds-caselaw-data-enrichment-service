module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.14.0"

  name = "${local.name}-vpc-${local.environment}"
  cidr = var.vpc_cidr_block

  azs              = ["${local.region}a", "${local.region}b"]
  public_subnets   = local.public_cidr_blocks
  database_subnets = local.database_cidr_blocks
  private_subnets  = local.private_cidr_blocks

  create_database_subnet_group       = true
  create_database_subnet_route_table = true
  create_database_nat_gateway_route  = true

  manage_default_security_group = true
  default_security_group_egress = [
    {
      description = "Allow calls to external"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      cidr_blocks = "0.0.0.0/0"
    },
    {
      description     = "Allow calls to rds database"
      protocol        = "tcp"
      from_port       = 5432
      to_port         = 5432
      security_groups = join(",", var.rds_security_group_ids)
    }
  ]

  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_support   = true
  enable_dns_hostnames = true
  single_nat_gateway   = local.vpc[local.environment].single_ngw

  tags = local.tags
}

# reusing this from data module
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [module.vpc.vpc_id]
  }

  filter {
    name   = "tag:Name"
    values = ["*-private-*"]
  }
}

data "aws_subnet" "private" {
  for_each = toset(data.aws_subnets.private.ids)
  id       = each.value
}

resource "aws_vpc_endpoint" "secrets_manager" {
  for_each = toset(data.aws_subnets.private.ids)

  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.eu-west-2.secretsmanager"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    module.vpc.default_security_group_id
  ]

  subnet_ids = [each.value]
}
