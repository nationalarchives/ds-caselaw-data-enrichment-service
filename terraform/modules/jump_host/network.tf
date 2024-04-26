resource "aws_security_group" "jump_host" {
  name        = "${local.name}-${local.environment}-jump-host"
  description = "${local.name} ${local.environment} jump host"
  vpc_id      = data.aws_subnet.jump_host.vpc_id
}

resource "aws_security_group_rule" "jump_host_all_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.jump_host.id
}
