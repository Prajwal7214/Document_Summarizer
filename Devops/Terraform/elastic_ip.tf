resource "aws_eip" "app" {
  domain = "vpc"

  instance = aws_instance.app.id

  tags = {
    Name        = "document-summarizer-eip"
    Environment = var.environment
    Project     = "DocumentSummarizer"
    ManagedBy   = "Terraform"
  }
}