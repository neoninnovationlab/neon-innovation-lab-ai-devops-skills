resource "aws_ebs_volume" "example_optimized" {
  availability_zone = "us-east-1a"
  size              = 100
  type              = "gp3"
}

resource "aws_cloudwatch_log_group" "app_logs_clean" {
  name              = "/aws/lambda/production-app-clean"
  retention_in_days = 90
}

resource "aws_s3_bucket" "cold_backups_clean" {
  bucket = "company-clean-backups"
}

resource "aws_s3_bucket_lifecycle_configuration" "cold_backups_rule" {
  bucket = aws_s3_bucket.cold_backups_clean.id

  rule {
    id     = "glacier-archive"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }
  }
}
