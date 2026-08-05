terraform {
  backend "s3" {
    bucket         = "document-summarizer-tfstate-2026"
    key            = "document-summarizer/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "document-summarizer-lock-table"
    encrypt        = true
  }
}