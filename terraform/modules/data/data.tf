data "aws_vpc" "vpc" {
  id = var.vpc_id
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  filter {
    name   = "tag:Name"
    values = ["*-public-*"]
  }
}

data "aws_subnet" "public" {
  for_each = toset(data.aws_subnets.public.ids)
  id       = each.value
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
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

data "aws_subnets" "database" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  filter {
    name   = "tag:Name"
    values = ["*-db-*"]
  }
}

data "aws_subnet" "database" {
  for_each = toset(data.aws_subnets.database.ids)
  id       = each.value
}

# data "aws_subnets" "db" {
#   filter {
#     name   = "vpc-id"
#     values = [var.vpc_id]
#   }

#   filter {
#     name   = "tag:Name"
#     values = ["*-db-*"]
#   }
# }
