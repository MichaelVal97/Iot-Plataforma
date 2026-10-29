output "primary_region" {
  description = "Región primaria de AWS"
  value       = var.aws_primary_region
}

output "dr_region" {
  description = "Región secundaria para Disaster Recovery"
  value       = var.aws_dr_region
}

output "backup_bucket_primary_name" {
  description = "Nombre del bucket S3 de backups en región primaria"
  value       = var.create_s3_backup_bucket ? aws_s3_bucket.backup_bucket_primary[0].id : "No creado"
}

output "backup_bucket_dr_name" {
  description = "Nombre del bucket S3 de backups en región DR"
  value       = var.create_s3_backup_bucket ? aws_s3_bucket.backup_bucket_dr[0].id : "No creado"
}

output "backup_bucket_primary_arn" {
  description = "ARN del bucket S3 de backups en región primaria"
  value       = var.create_s3_backup_bucket ? aws_s3_bucket.backup_bucket_primary[0].arn : "No creado"
}

output "backup_tracker_table_name" {
  description = "Nombre de la tabla DynamoDB para rastreo de backups"
  value       = var.create_dynamodb_backup ? aws_dynamodb_table.backup_tracker[0].name : "No creada"
}

output "backup_tracker_table_arn" {
  description = "ARN de la tabla DynamoDB para rastreo de backups"
  value       = var.create_dynamodb_backup ? aws_dynamodb_table.backup_tracker[0].arn : "No creada"
}

output "cloudwatch_log_group_name" {
  description = "Nombre del CloudWatch Log Group"
  value       = var.enable_cloudwatch_monitoring ? aws_cloudwatch_log_group.iot_platform_logs[0].name : "No creado"
}

output "sns_topic_arn" {
  description = "ARN del SNS Topic para alertas"
  value       = var.enable_cloudwatch_monitoring ? aws_sns_topic.iot_platform_alerts[0].arn : "No creado"
}

output "account_id" {
  description = "ID de la cuenta AWS"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_profile_used" {
  description = "Perfil AWS utilizado"
  value       = var.aws_profile
}

output "environment" {
  description = "Ambiente de Terraform"
  value       = var.environment
}

output "project_name" {
  description = "Nombre del proyecto"
  value       = var.project_name
}

output "rpo_minutes" {
  description = "Objetivo de Punto de Recuperación (en minutos)"
  value       = var.rpo_minutes
}

output "rto_minutes" {
  description = "Objetivo de Tiempo de Recuperación (en minutos)"
  value       = var.rto_minutes
}

output "cluster_connection_string" {
  description = "Connection string del cluster MongoDB Atlas"
  value       = mongodbatlas_cluster.atlas_cluster.connection_strings[0].standard_srv
  sensitive   = true
}

output "cluster_id" {
  description = "ID del cluster MongoDB Atlas"
  value       = mongodbatlas_cluster.atlas_cluster.id
}

output "cluster_info" {
  description = "Información resumida del cluster MongoDB Atlas"
  value = {
    backup      = mongodbatlas_cluster.atlas_cluster.backup_enabled
    disk_gb     = mongodbatlas_cluster.atlas_cluster.disk_size_gb
    instance    = mongodbatlas_cluster.atlas_cluster.provider_instance_size_name
    name        = mongodbatlas_cluster.atlas_cluster.name
    provider    = mongodbatlas_cluster.atlas_cluster.provider_name
    region      = mongodbatlas_cluster.atlas_cluster.provider_region_name
    replication = "${mongodbatlas_cluster.atlas_cluster.replication_factor} nodes (REPLICASET)"
  }
}

output "cluster_state" {
  description = "Estado del cluster MongoDB Atlas"
  value       = mongodbatlas_cluster.atlas_cluster.state_name
}

output "database_username" {
  description = "Usuario de base de datos MongoDB Atlas"
  value       = var.atlas_db_user_username
}

output "project_id" {
  description = "ID del proyecto MongoDB Atlas"
  value       = var.atlas_project_id
}

output "dr_setup_instructions" {
  description = "Instrucciones para configurar Disaster Recovery"
  value       = <<-EOT
    
    =============================================================================
    INSTRUCCIONES DE CONFIGURACIÓN DE DISASTER RECOVERY
    =============================================================================
    
    1. CONFIGURACIÓN DE MONGODB ATLAS:
       - Crear o modificar cluster para habilitar Multi-Region Replication
       - Regiones recomendadas:
         * Primaria: us-east-1
         * Secundaria: us-west-2
       - En Atlas Console: Deployment → Replication
       - Cambio de región puede tomar 5-10 minutos
    
    2. CONFIGURACIÓN DE BACKUPS EN ATLAS:
       - Deployment → Backup
       - Habilitar Continuous Backups (si está disponible)
       - Backup Frequency: Cada 6 horas (mínimo recomendado)
       - Backup Retention: 7 días (recomendado)
    
    3. VERIFICAR REPLICACIÓN:
       - Conectar desde ambas regiones
       - Insertar datos en primaria
       - Verificar que aparezcan en secundaria en < 1 segundo
    
    4. PLAN DE RECUPERACIÓN:
       - Ver: docs/disaster-recovery.md
       - Documento contiene procedimiento completo
    
    5. VALIDACIÓN:
       - Ejecutar: python scripts/verify_dr.py --full
       - Verifica configuración básica
       - Proporciona guía para validaciones manuales
    
    =============================================================================
  EOT
}
