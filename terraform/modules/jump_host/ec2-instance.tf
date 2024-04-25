resource "aws_launch_template" "jump_host" {
  name        = "${local.name}-${local.environment}-jump-host"
  description = "${local.name} ${local.environment} jump host"

  block_device_mappings {
    # Root EBS volume
    device_name = "/dev/xvda"

    ebs {
      volume_size           = 50
      encrypted             = true
      delete_on_termination = true
    }
  }

  network_interfaces {
    associate_public_ip_address = false
    subnet_id                   = local.subnet_id
    security_groups             = [aws_security_group.jump_host.id]
  }

  iam_instance_profile {
    name = aws_iam_instance_profile.jump_host.name
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  monitoring {
    enabled = true
  }

  disable_api_termination              = false
  disable_api_stop                     = false
  ebs_optimized                        = true
  image_id                             = data.aws_ami.jump_host.id
  instance_initiated_shutdown_behavior = "stop"
  instance_type                        = local.instance_type

  user_data = templatefile("${path.module}/ec2-userdata/jump-host.tpl", {})
}

resource "aws_instance" "jump_host" {
  launch_template {
    id      = aws_launch_template.jump_host.id
    version = "$Latest"
  }

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted = true
  }

  tags = {
    Name = "${local.name}-${local.environment}-jump-host"
  }
}
