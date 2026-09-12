resource "aws_ebs_volume" "example_wasteful" {
  availability_zone = "us-east-1a"
  size              = 100
  type              = "gp2"
}

resource "aws_cloudwatch_log_group" "app_logs" {
  name = "/aws/lambda/production-app"
  # Missing retention_in_days (defaults to Never Expire)
}

resource "aws_s3_bucket" "cold_backups" {
  bucket = "company-raw-backups-archive"
  # Missing aws_s3_bucket_lifecycle_configuration
}

resource "aws_instance" "bastion" {
  ami                         = "ami-12345678"
  instance_type               = "t3.micro"
  associate_public_ip_address = true
}

resource "aws_db_instance" "dev_database" {
  identifier        = "company-dev-db"
  allocated_storage = 50
  storage_type      = "io1"
  engine            = "postgres"
  instance_class    = "db.m5.large"
  multi_az          = true
}
