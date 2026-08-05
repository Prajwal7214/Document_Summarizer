

resource "aws_instance" "app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.main.id]
  key_name               = var.key_name

  associate_public_ip_address = true

  disable_api_termination = true

  user_data = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true

    tags = {
      Name = "document-summarizer-root-volume"
    }
  }

  tags = {
    Name = "document-summarizer-ec2"
  }

  lifecycle {
    ignore_changes = [
      user_data
    ]
  }
}
