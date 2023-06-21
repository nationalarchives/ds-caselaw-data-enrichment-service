module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = ">=5.0.0,<6.0.0"

  name = "${local.name}-vpc-${local.environment}"
  cidr = var.vpc_cidr_block

  azs              = ["${local.region}a", "${local.region}b"]
  public_subnets   = local.public_cidr_blocks
  database_subnets = local.database_cidr_blocks
  private_subnets  = local.private_cidr_blocks
  #   redshift_subnets = local.redshift_cidr_blocks

  create_database_subnet_group       = true
  create_database_subnet_route_table = true
  create_database_nat_gateway_route  = true
  #create_database_internet_gateway_route = true

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
      security_groups = var.rds_security_group_id
    }
  ]

  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_support   = true
  enable_dns_hostnames = true
  #single_nat_gateway     = true
  single_nat_gateway = local.vpc[local.environment].single_ngw
  #one_nat_gateway_per_az = false

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
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.eu-west-2.secretsmanager"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    # aws_default_vpc.csx_default.default_security_group_id,
    module.vpc.default_security_group_id
  ]

  # subnet_ids = local.private_cidr_blocks
  # subnet_ids = [module.vpc.public_subnets]
  # subnet_ids = ["subnet-0294f174fda94e874","subnet-0a75c1dc97fe38ac2"]
  # for_each = toset(module.vpc.public_subnets)
  # subnet_ids = "${element(var.subnet_azs, count.index)}"
  # subnet_ids =each.key

  # ￼count = "${length(module.vpc.public_subnets.ids)}"
  # ￼  subnet_ids = "${element(tolist(module.vpc.public_subnets.ids), count.index)}"
  # subnet_ids = "${tolist(module.vpc.public_subnets.ids)}"
  # subnet_ids = "${tolist(module.vpc.public_subnets).ids}"
  # subnet_ids = ["${module.vpc.public_subnets}"]

  # "module": "module.data",
  # "mode": "data",
  # "type": "aws_subnet",
  # "name": "private",

  # subnet_ids = [for value in module.vpc.public_subnets: value.id]
  for_each = toset(data.aws_subnets.private.ids)
  # id       = each.value
  subnet_ids = [each.value]

  # private_dns_enabled = true
}
# ": "sg-0216fc2f7477ed58d",

# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = aws_default_vpc.csx_default.id
#   service_name      = "com.amazonaws.eu-west-2.s3"
#   route_table_ids   = [aws_default_vpc.csx_default.main_route_table_id]
# }

# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.s3"
#   vpc_endpoint_type = "Interface"

#   security_group_ids = [
#     module.s3_gateway_endpoint_sg.security_group_id
#   ]

#   private_dns_enabled = false

#   tags = merge(local.tags, {
#     Name = "${local.name}-s3-gateway-endpoint-${local.environment}"
#   })
# }

# resource "aws_vpc_endpoint_subnet_association" "s3_gateway_subnet" {
#   vpc_endpoint_id = aws_vpc_endpoint.s3.id
#   subnet_id       = aws_subnet.storage_gateway_subnet.id
# }

# resource "aws_subnet" "storage_gateway_subnet" {
#   vpc_id     = module.vpc.vpc_id
#   cidr_block = local.gateway_cidr_block

#   tags = merge(local.tags, {
#     Name = "${local.name}-storage-gateway-subnet-${local.environment}"
#   })
# }

# resource "aws_route_table" "storage_gateway_vpn" {
#   vpc_id = module.vpc.vpc_id

#   tags = merge(local.tags, {
#     Name = "${local.name}-storage-gateway-vpn-route-${local.environment}"
#   })
# }

# resource "aws_route_table_association" "storage_gateway_vpn" {
#   subnet_id      = aws_subnet.storage_gateway_subnet.id
#   route_table_id = aws_route_table.storage_gateway_vpn.id
# }

# module "storage_gateway_endpoint_sg" {
#   source  = "terraform-aws-modules/security-group/aws"
#   version = ">=4.0.0,<=5.0.0"

#   name   = "${local.name}-storage-gateway-sg-${local.environment}"
#   vpc_id = module.vpc.vpc_id

#   ingress_with_cidr_blocks = [
#     {
#       rule        = "ssh-tcp"
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       rule        = "rdp-tcp"
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       rule        = "all-icmp"
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       rule        = "https-443-tcp"
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       protocol    = 6
#       from_port   = 1026
#       to_port     = 1028
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       protocol    = 6
#       from_port   = 1031
#       to_port     = 1031
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       protocol    = 6
#       from_port   = 2222
#       to_port     = 2222
#       cidr_blocks = var.azure_cidr_block
#     }
#   ]

#   egress_with_cidr_blocks = [
#     {
#       protocol    = "-1"
#       from_port   = 0
#       to_port     = 0
#       cidr_blocks = var.azure_cidr_block
#     }
#   ]
# }

# resource "aws_vpc_endpoint" "storage_gateway" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.storagegateway"
#   vpc_endpoint_type = "Interface"

#   security_group_ids = [
#     module.storage_gateway_endpoint_sg.security_group_id
#   ]

#   private_dns_enabled = false

#   tags = merge(local.tags, {
#     Name = "${local.name}-storage-gateway-endpoint-${local.environment}"
#   })
# }

# resource "aws_vpc_endpoint_subnet_association" "storage_gateway_subnet" {
#   vpc_endpoint_id = aws_vpc_endpoint.storage_gateway.id
#   subnet_id       = aws_subnet.storage_gateway_subnet.id
# }

# module "s3_gateway_endpoint_sg" {
#   source  = "terraform-aws-modules/security-group/aws"
#   version = ">=4.0.0,<=5.0.0"

#   name   = "${local.name}-s3-gateway-sg-${local.environment}"
#   vpc_id = module.vpc.vpc_id

#   ingress_with_cidr_blocks = [
#     {
#       rule        = "ssh-tcp"
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       rule        = "https-443-tcp"
#       cidr_blocks = var.azure_cidr_block
#     }
#   ]

#   egress_with_cidr_blocks = [
#     {
#       rule        = "ssh-tcp"
#       cidr_blocks = var.azure_cidr_block
#     },
#     {
#       rule        = "https-443-tcp"
#       cidr_blocks = var.azure_cidr_block
#     }
#   ]
# }


# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.s3"
#   vpc_endpoint_type = "Interface"

#   security_group_ids = [
#     module.s3_gateway_endpoint_sg.security_group_id
#   ]

#   private_dns_enabled = false

#   tags = merge(local.tags, {
#     Name = "${local.name}-s3-gateway-endpoint-${local.environment}"
#   })
# }

# resource "aws_vpc_endpoint_subnet_association" "s3_gateway_subnet" {
#   vpc_endpoint_id = aws_vpc_endpoint.s3.id
#   subnet_id       = aws_subnet.storage_gateway_subnet.id
# }

# module "fargate_endpoints_sg" {
#   source  = "terraform-aws-modules/security-group/aws"
#   version = ">=4.0.0,<=5.0.0"

#   name   = "${local.name}-fargate-endpoints-sg-${local.environment}"
#   vpc_id = module.vpc.vpc_id

#   ingress_with_cidr_blocks = [
#     {
#       rule        = "https-443-tcp"
#       cidr_blocks = module.vpc.vpc_cidr_block
#     }
#   ]

#   egress_with_cidr_blocks = [
#     {
#       rule        = "https-443-tcp"
#       cidr_blocks = "0.0.0.0/0"
#     }
#   ]
# }

# locals {
#   fargate_vpc_endpoints = [
#     "secretsmanager",
#     "ecr.dkr",
#     "ecr.api",
#     "logs"
#   ]
# }

# resource "aws_vpc_endpoint" "fargate" {
#   for_each = toset(local.fargate_vpc_endpoints)

#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.${each.value}"
#   vpc_endpoint_type = "Interface"

#   security_group_ids = [
#     module.fargate_endpoints_sg.security_group_id
#   ]

#   subnet_ids = module.vpc.public_subnets

#   private_dns_enabled = true

#   tags = merge(local.tags, {
#     Name = "${local.name}-${each.value}-endpoint-${local.environment}"
#   })
# }
