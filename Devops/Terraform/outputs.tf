output "instance_public_ip" {
  description = "Public IP of EC2"

  value = aws_instance.app.public_ip
}

output "instance_public_dns" {
  description = "Public DNS"

  value = aws_instance.app.public_dns
}

output "instance_id" {
  value = aws_instance.app.id
}

output "elastic_ip" {
  description = "Elastic IP address"
  value       = aws_eip.app.public_ip
}