# =============================================================================
# IoT Platform Infrastructure as Code
# =============================================================================
# Infraestructura AWS para soportar IoT Platform con MongoDB Atlas
# Incluye recursos para Disaster Recovery, backups y monitoreo
# =============================================================================

# S3 Bucket para backups (Región Primaria)
# Nota: Este bucket es para almacenar backups de MongoDB Atlas, no los datos IoT
resource "aws_s3_bucket" "backup_bucket_primary" {
  count  = var.create_s3_backup_bucket ? 1 : 0
  bucket = "${var.project_name}-backups-primary-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    var.tags,
    {
      Name   = "${var.project_name}-backups-primary"
      Region = var.aws_primary_region
    }
  )
}

# Versioning para backups
resource "aws_s3_bucket_versioning" "backup_versioning_primary" {
  count  = var.create_s3_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backup_bucket_primary[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encriptación de bucket de backups
resource "aws_s3_bucket_server_side_encryption_configuration" "backup_encryption" {
  count  = var.create_s3_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backup_bucket_primary[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy para backups (Transición a Glacier después de 30 días)
resource "aws_s3_bucket_lifecycle_configuration" "backup_lifecycle" {
  count  = var.create_s3_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backup_bucket_primary[0].id

  rule {
    id     = "backup-transition"
    status = "Enabled"
    filter {}

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = var.backup_retention_days * 2 # Mantener copias por más tiempo
    }
  }
}

# S3 Bucket para Disaster Recovery (Región DR)
resource "aws_s3_bucket" "backup_bucket_dr" {
  count    = var.create_s3_backup_bucket ? 1 : 0
  provider = aws.dr
  bucket   = "${var.project_name}-backups-dr-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    var.tags,
    {
      Name   = "${var.project_name}-backups-dr"
      Region = var.aws_dr_region
    }
  )
}

# Replicación entre buckets (Primario → DR)
resource "aws_s3_bucket_replication_configuration" "backup_replication" {
  count      = var.create_s3_backup_bucket ? 1 : 0
  depends_on = [aws_s3_bucket_versioning.backup_versioning_primary[0]]

  bucket = aws_s3_bucket.backup_bucket_primary[0].id

  role = aws_iam_role.s3_replication_role[0].arn

  rule {
    id     = "backup-replication"
    status = "Enabled"

    filter {
      prefix = "backups/"
    }

    destination {
      bucket        = aws_s3_bucket.backup_bucket_dr[0].arn
      storage_class = "STANDARD_IA"

      replication_time {
        status = "Enabled"
        time {
          minutes = 15 # RTO: 15 minutos
        }
      }

      metrics {
        status = "Enabled"
        event_threshold {
          minutes = 15
        }
      }
    }
  }
}

# DynamoDB Table para rastreo de backups (Región Primaria)
resource "aws_dynamodb_table" "backup_tracker" {
  count            = var.create_dynamodb_backup ? 1 : 0
  name             = "${var.project_name}-backup-tracker"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "backup_id"
  stream_view_type = "NEW_AND_OLD_IMAGES"
  stream_enabled   = true

  attribute {
    name = "backup_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-backup-tracker"
    }
  )
}

# CloudWatch Log Group para monitoreo (Región Primaria)
resource "aws_cloudwatch_log_group" "iot_platform_logs" {
  count             = var.enable_cloudwatch_monitoring ? 1 : 0
  name              = "/aws/iot-platform/${var.project_name}"
  retention_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-logs"
    }
  )
}

# CloudWatch Alarm para monitoreo de backups
resource "aws_cloudwatch_metric_alarm" "backup_failure" {
  count               = var.create_dynamodb_backup && var.enable_cloudwatch_monitoring ? 1 : 0
  alarm_name          = "${var.project_name}-backup-failure"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "FailedBackupCount"
  namespace           = "AWS/DynamoDB"
  period              = 3600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alerta cuando hay fallos en el backup"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.backup_tracker[0].name
  }
}

# SNS Topic para notificaciones (Región Primaria)
resource "aws_sns_topic" "iot_platform_alerts" {
  count = var.enable_cloudwatch_monitoring ? 1 : 0
  name  = "${var.project_name}-alerts"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-alerts"
    }
  )
}

# IAM Role para S3 Replication
resource "aws_iam_role" "s3_replication_role" {
  count = var.create_s3_backup_bucket ? 1 : 0
  name  = "${var.project_name}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy para S3 Replication
resource "aws_iam_role_policy" "s3_replication_policy" {
  count = var.create_s3_backup_bucket ? 1 : 0
  name  = "${var.project_name}-s3-replication-policy"
  role  = aws_iam_role.s3_replication_role[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.backup_bucket_primary[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl"
        ]
        Resource = "${aws_s3_bucket.backup_bucket_primary[0].arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete"
        ]
        Resource = "${aws_s3_bucket.backup_bucket_dr[0].arn}/*"
      }
    ]
  })
}

# MongoDB Atlas resources to mirror the project plan shown in the walkthrough
resource "mongodbatlas_cluster" "atlas_cluster" {
  project_id                  = var.atlas_project_id
  name                        = var.atlas_cluster_name
  provider_name               = "AWS"
  provider_region_name        = "US_EAST_1"
  provider_instance_size_name = "M10"
  backup_enabled              = true
  provider_volume_type        = "STANDARD"
  provider_disk_iops          = 300
  cluster_type                = "REPLICASET"
  replication_factor          = 3
  mongo_db_major_version      = "7.0"
}

import {
  to = mongodbatlas_cluster.atlas_cluster
  id = "${var.atlas_project_id}-${var.atlas_cluster_name}"
}

# Data source para obtener información de la cuenta
data "aws_caller_identity" "current" {}

# Data source para obtener regiones
data "aws_regions" "all" {}
