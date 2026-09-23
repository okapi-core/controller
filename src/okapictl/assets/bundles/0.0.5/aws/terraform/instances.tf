resource "aws_instance" "okapi" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.okapi_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.okapi.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.instance.name
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/templates/user-data.sh.tftpl", {
    project_name = var.project_name
    role         = "okapi-stack"
    aws_region   = var.aws_region
  })

  root_block_device {
    volume_size           = var.root_volume_size_gb
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  tags = local.okapi_tags
}

resource "aws_instance" "otel" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.otel_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.otel.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.instance.name
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/templates/user-data.sh.tftpl", {
    project_name = var.project_name
    role         = "otel-demo"
    aws_region   = var.aws_region
  })

  root_block_device {
    volume_size           = var.root_volume_size_gb
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  tags = local.otel_tags
}

resource "aws_ebs_volume" "okapi_data" {
  availability_zone = aws_subnet.public.availability_zone
  size              = var.okapi_data_volume_size_gb
  type              = "gp3"
  encrypted         = true

  tags = merge(local.tags, {
    Name = "${var.project_name}-okapi-data"
  })
}

resource "aws_volume_attachment" "okapi_data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.okapi_data.id
  instance_id = aws_instance.okapi.id
}

resource "aws_eip" "okapi" {
  domain = "vpc"

  tags = merge(local.tags, {
    Name = "${var.project_name}-okapi"
  })
}

resource "aws_eip_association" "okapi" {
  allocation_id = aws_eip.okapi.id
  instance_id   = aws_instance.okapi.id
}

resource "aws_eip" "otel" {
  domain = "vpc"

  tags = merge(local.tags, {
    Name = "${var.project_name}-otel"
  })
}

resource "aws_eip_association" "otel" {
  allocation_id = aws_eip.otel.id
  instance_id   = aws_instance.otel.id
}
