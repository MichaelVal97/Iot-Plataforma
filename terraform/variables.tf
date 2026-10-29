variable "aws_profile" {
  description = "Perfil AWS a utilizar"
  type        = string
  default     = "default"
}

variable "aws_primary_region" {
  description = "Región primaria de AWS"
  type        = string
  default     = "us-east-1"
}

variable "aws_dr_region" {
  description = "Región secundaria para Disaster Recovery"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "iot-platform"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser dev, staging o prod."
  }
}

variable "create_s3_backup_bucket" {
  description = "Crear bucket S3 para backups"
  type        = bool
  default     = false
}

variable "create_dynamodb_backup" {
  description = "Crear tabla DynamoDB para backups"
  type        = bool
  default     = false
}

variable "create_iam_roles" {
  description = "Crear roles IAM para acceso a MongoDB"
  type        = bool
  default     = false
}

variable "enable_cloudwatch_monitoring" {
  description = "Habilitar CloudWatch para monitoreo"
  type        = bool
  default     = false
}

variable "mongodb_connection_uri" {
  description = "URI de conexión a MongoDB Atlas (sensible, no usar en versiones de control)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "backup_retention_days" {
  description = "Días de retención de backups"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Retención debe estar entre 1 y 365 días."
  }
}

variable "rpo_minutes" {
  description = "Objetivo de Punto de Recuperación en minutos"
  type        = number
  default     = 60
}

variable "rto_minutes" {
  description = "Objetivo de Tiempo de Recuperación en minutos"
  type        = number
  default     = 15
}

variable "atlas_public_key" {
  description = "MongoDB Atlas public key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "atlas_private_key" {
  description = "MongoDB Atlas private key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "atlas_project_id" {
  description = "MongoDB Atlas project ID containing the existing cluster"
  type        = string
}

variable "atlas_cluster_name" {
  description = "MongoDB Atlas cluster name"
  type        = string
  default     = "ClusterParcial"
}

variable "atlas_db_user_username" {
  description = "MongoDB Atlas database user"
  type        = string
  default     = "stretch394_db_user"
}

variable "tags" {
  description = "Tags adicionales para aplicar a todos los recursos"
  type        = map(string)
  default     = {}
}
