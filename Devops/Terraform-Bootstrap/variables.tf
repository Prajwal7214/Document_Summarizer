variable "aws_region" {
  default = "ap-south-1"
}

variable "bucket_name" {
  description = "Terraform state bucket name"
}

variable "dynamodb_table_name" {
  description = "Terraform lock table"
}