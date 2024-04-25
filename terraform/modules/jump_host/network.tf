resource "aws_security_group" "jump_host" {
  name        = "${local.name}-${local.environment}-jump-host"
  description = "${local.name} ${local.environment} jump host"
  vpc_id      = data.aws_subnet.jump_host.vpc_id
}
