# Requisito 16: Infrastructure as Code (Terraform)

## Objetivo

Definir toda la infraestructura AWS mediante Terraform.

## Estado de validación

La configuración pasó `terraform fmt -check -recursive` y `terraform validate` con Terraform 1.16.2 y el provider AWS 5.100.0. La validación se hizo con backend desactivado; no se usaron credenciales, no se ejecutó `terraform plan` y no se crearon recursos AWS. El DR de la entrega se prueba aparte mediante simulación local.

Evidencias ejecutadas:
- `terraform_fmt.txt`
- `terraform_validate.txt`

Repetir la validación desde la raíz del proyecto:

```powershell
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate
terraform -chdir=terraform fmt -check -recursive
```

## Estructura de Terraform

```
terraform/
├── providers.tf          # Proveedores (AWS primaria + DR)
├── variables.tf          # Variables de entrada
├── main.tf               # Recursos principales
├── outputs.tf            # Salidas / outputs
└── terraform.tfvars.example  # Archivo de ejemplo
```

## Archivos Terraform

### 1. providers.tf

**Función**: Define proveedores y configuración global

**Contenido**:
- Provider AWS (primaria)
- Provider AWS alias (DR)
- Backend S3 (comentado, para activar después)
- Default tags para todos los recursos

**Regiones**:
- Primaria: `us-east-1` (configurable)
- DR: `us-west-2` (configurable)

### 2. variables.tf

**Función**: Define todas las variables de entrada

**Variables principales**:
- `aws_profile`: Perfil AWS a usar
- `aws_primary_region`: Región primaria
- `aws_dr_region`: Región de DR
- `project_name`: Nombre del proyecto
- `environment`: dev/staging/prod
- `backup_retention_days`: Días de retención
- `rpo_minutes`: Objetivo de punto de recuperación
- `rto_minutes`: Objetivo de tiempo de recuperación

**Variables de recursos** (condicionales):
- `create_s3_backup_bucket`: Crear buckets S3
- `create_dynamodb_backup`: Crear tabla DynamoDB
- `create_iam_roles`: Crear roles IAM
- `enable_cloudwatch_monitoring`: Monitoreo

### 3. main.tf

**Función**: Define recursos AWS

**Recursos creados**:

#### S3 Buckets (Primaria)
```
aws_s3_bucket
  ├── Bucket principal: iot-platform-backups-primary-{ACCOUNT}
  ├── Versioning habilitado
  ├── Encriptación AES256
  └── Lifecycle: Transición a Glacier después de 30 días
```

#### S3 Buckets (DR)
```
aws_s3_bucket
  ├── Bucket DR: iot-platform-backups-dr-{ACCOUNT}
  ├── Replicación desde primario
  └── Storage class: STANDARD_IA
```

#### S3 Replicación
```
aws_s3_bucket_replication_configuration
  ├── Fuente: us-east-1
  ├── Destino: us-west-2
  ├── RTC: 15 minutos
  └── Métricas habilitadas
```

#### DynamoDB (Rastreo)
```
aws_dynamodb_table
  ├── Nombre: iot-platform-backup-tracker
  ├── Billing mode: PAY_PER_REQUEST
  ├── Hash key: backup_id
  ├── Global secondary index: timestamp
  └── TTL: expiration_time
```

#### CloudWatch
```
aws_cloudwatch_log_group
  ├── Nombre: /aws/iot-platform/iot-platform
  ├── Retención: 30 días
  └── SNS Alarms para fallos
```

#### SNS
```
aws_sns_topic
  ├── Nombre: iot-platform-alerts
  └── Para notificaciones de fallos
```

#### IAM
```
aws_iam_role
  ├── S3 Replication Role
  ├── Permisos mínimos requeridos
  └── Trust policy para S3
```

### 4. outputs.tf

**Función**: Define salidas de Terraform

**Outputs principales**:
- `primary_region`: Región primaria usada
- `dr_region`: Región DR usada
- `backup_bucket_primary_name`: Nombre del bucket primario
- `backup_bucket_dr_name`: Nombre del bucket DR
- `account_id`: ID de cuenta AWS
- `rpo_minutes` / `rto_minutes`: Objetivos de recuperación
- `dr_setup_instructions`: Guía de configuración

## Configuración y Ejecución

### Paso 1: Instalación de Terraform

```powershell
# Descargar desde https://www.terraform.io/downloads.html
# O usar chocolatey (si está instalado)
choco install terraform

# Verificar instalación
terraform version
# Resultado: Terraform v1.X.X
```

### Paso 2: Configuración de AWS

```powershell
# Instalar AWS CLI
pip install awscli

# Configurar credenciales
aws configure --profile default

# Parámetros a ingresar:
# AWS Access Key ID: [tu_key]
# AWS Secret Access Key: [tu_secret]
# Default region: us-east-1
# Default output format: json

# Verificar configuración
aws sts get-caller-identity
# Resultado: mostrará Account ID, ARN, Usuario
```

### Paso 3: Preparar Terraform

```powershell
# Ir a directorio terraform
cd terraform

# Copiar archivo de ejemplo
Copy-Item terraform.tfvars.example terraform.tfvars

# Editar configuración
notepad terraform.tfvars

# Configurar valores:
aws_profile = "default"
aws_primary_region = "us-east-1"
aws_dr_region = "us-west-2"
project_name = "iot-platform"
environment = "dev"

# Por ahora, DESACTIVAR recursos costosos:
# create_s3_backup_bucket = false
# create_dynamodb_backup = false
# enable_cloudwatch_monitoring = false
```

### Paso 4: Inicializar Terraform

```powershell
# En directorio terraform/
terraform init

# Resultado esperado:
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully initialized!
```

### Paso 5: Validar Configuración

```powershell
# Validar sintaxis
terraform validate

# Resultado esperado:
# Success! The configuration is valid.

# Formater (limpia indentación)
terraform fmt

# Verificar que se limpió
terraform fmt -check
```

### Paso 6: Ver Plan (SIN CREAR RECURSOS)

```powershell
# Ver qué se va a crear
terraform plan -out=plan.tfplan

# Resultado: Mostrará:
# Plan: X to add, 0 to change, 0 to destroy

# Guardar plan para evidencia
terraform plan > ..\evidencias\requisito-16\plan.txt
```

### Paso 7: Aplicar (SOLO SI ESTÁ LISTO)

```powershell
# IMPORTANTE: Esto creará recursos y puede generar COSTOS

# Aplicar plan
terraform apply plan.tfplan

# O apply directo (pide confirmación)
terraform apply

# Resultado: Mostrará outputs
# Ejemplo:
# primary_region = "us-east-1"
# account_id = "123456789012"
```

### Paso 8: Obtener Salidas

```powershell
# Ver outputs (después de apply)
terraform output

# Salida específica
terraform output account_id
terraform output backup_bucket_primary_name
```

## Validaciones Sin Crear Recursos

```powershell
# SOLO VALIDAR, SIN CREAR

cd terraform

# 1. Inicializar
terraform init

# 2. Validar sintaxis
terraform validate

# 3. Formater
terraform fmt

# 4. Ver plan (sin aplicar)
terraform plan > ../evidencias/requisito-16/plan.txt

# 5. Validar recursos específicos
terraform validate

# Resultado: Todo OK sin crear nada
```

## Archivos de Evidencia

### 1. Plan Output

```powershell
# Capturar plan
terraform plan > ../evidencias/requisito-16/plan.txt

# Contenido esperado:
# Terraform will perform the following actions:
# 
# # aws_s3_bucket.backup_bucket_primary[0] will be created
#   + bucket                  = "iot-platform-backups-primary-123456789012"
#   ...
# 
# Plan: 8 to add, 0 to change, 0 to destroy
```

### 2. Validate Output

```powershell
terraform validate > ../evidencias/requisito-16/validate.txt

# Resultado esperado:
# Success! The configuration is valid.
```

### 3. Format Check

```powershell
terraform fmt -check

# Resultado esperado:
# (sin salida = todo bien)
```

### 4. Archivos Terraform

Copiar archivos para evidencia:
- `providers.tf`
- `variables.tf`
- `main.tf`
- `outputs.tf`

## Recursos Definidos

### Recursos OPTIONALES (Desactivados por defecto)

```hcl
# S3 Backups
create_s3_backup_bucket = false
# Costo: ~$0.023/GB/mes

# DynamoDB
create_dynamodb_backup = false
# Costo: ~$1.25/millón escrituras (bajo uso)

# CloudWatch
enable_cloudwatch_monitoring = false
# Costo: ~$0.50/GB logs
```

### Recursos GRATUITOS (Siempre disponibles)

```hcl
# IAM Roles
create_iam_roles = true
# Costo: $0 (gratuito)

# Outputs e información
# Costo: $0 (no consume recursos)
```

## Estructura de Estado

### Backend Local (Por defecto)

```
terraform.tfstate    # Estado actual (NO COMMITEAR)
terraform.tfstate.backup  # Backup anterior
```

### Backend Remoto (Opcional - Comentado)

```hcl
# Para activar, descomentar en providers.tf:
backend "s3" {
  bucket         = "iot-platform-terraform-state"
  key            = "prod/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-locks"
}
```

## Variables de Entorno (Alternativo)

```powershell
# En lugar de terraform.tfvars, puedes usar variables de entorno:

$env:TF_VAR_aws_primary_region = "us-east-1"
$env:TF_VAR_aws_dr_region = "us-west-2"
$env:TF_VAR_project_name = "iot-platform"
$env:TF_VAR_environment = "dev"

# Luego ejecutar:
terraform plan
```

## Seguridad

### Datos Sensibles

❌ **NO hacer**:
- Commitear terraform.tfstate
- Escribir credenciales en archivos
- Compartir terraform.tfvars público

✅ **Hacer**:
- terraform.tfstate en .gitignore
- Usar variables de entorno
- Usar AWS profiles
- terraform.tfvars.example como plantilla

### Permisos Mínimos

El IAM user debe tener:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "dynamodb:*",
        "cloudwatch:*",
        "sns:*",
        "iam:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Costo Estimado

### Configuración: All Disabled (Recomendada inicialmente)

```
S3: $0 (no creado)
DynamoDB: $0 (no creado)
CloudWatch: $0 (no creado)
SNS: $0 (no creado)
IAM: $0 (gratuito)
━━━━━━━━━━━━━━━━━━
Total: $0/mes
```

### Configuración: All Enabled (Producción)

```
S3 (50GB): $1.15/mes
S3 Replication: $1.00/mes (50GB)
DynamoDB: $0.01-1.00/mes
CloudWatch: $5-10/mes (logs + alarms)
SNS: $0.01/mes
IAM: $0 (gratuito)
━━━━━━━━━━━━━━━━━━
Total: ~$10-15/mes + MongoDB Atlas
```

## Troubleshooting

### Credential Error

```
Error: error configuring AWS SDK: NoCredentialProviders
```

**Solución**:
```powershell
aws configure --profile default
aws sts get-caller-identity
```

### Region Not Available

```
Error: Error getting AZ information
```

**Solución**:
- Verificar región está disponible
- Usar us-east-1 (siempre disponible)
- Cambiar en variables.tf

### Bucket Already Exists

```
Error: Error creating S3 bucket: BucketAlreadyExists
```

**Solución**:
- Nombre de bucket es global único
- Cambiar project_name en terraform.tfvars

## Referencias

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [S3 Cross-Region Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [DynamoDB with Terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table)
- Código fuente: `terraform/*.tf`
