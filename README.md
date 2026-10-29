# IoT Platform - Proyecto Académico

Plataforma IoT basada en **MongoDB** y **Python**, con escenarios académicos simulados localmente. No requiere aprovisionar AWS para ejecutar las simulaciones; Terraform se conserva como definición de infraestructura de referencia.

## 📋 Estado de Requisitos

| Requisito | Descripción | Estado |
|-----------|-------------|--------|
| **13** | Almacenar datos de sensores IoT y escalar a 50+ GB | ✓ Simulación local con objetivo de 50 GB cumplido en la proyección |
| **14** | Disaster Recovery cross-region | ✓ Failover simulado con réplica local y recuperación verificada |
| **15** | Dashboard de monitoreo en Python/Matplotlib | ✓ Dashboard y métricas generadas en modo demo |
| **16** | Infrastructure as Code con Terraform | ✓ Código formateado y validado localmente; sin despliegue AWS |
| **17** | Catálogo de datos | ✓ Generador JSON/Markdown para las colecciones IoT |

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                  IoT Platform                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Python Scripts                                  │  │
│  │  ├── generar_datos_iot.py (Generación)          │  │
│  │  ├── verificar_tamano_mongodb.py (Validación)   │  │
│  │  ├── verify_dr.py (DR)                          │  │
│  │  └── dashboard_monitoreo.py (Visualización)     │  │
│  └──────────────────────────────────────────────────┘  │
│                      ↓                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  MongoDB Atlas (OLTP)                            │  │
│  │  ├── Primaria: us-east-1                        │  │
│  │  └── Secundaria: us-west-2 (DR)                 │  │
│  └──────────────────────────────────────────────────┘  │
│                      ↓ ETL por lotes                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  BigQuery Sandbox (OLAP)                         │  │
│  │  ├── dim_sensors                                 │  │
│  │  └── fact_readings                               │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  AWS Infrastructure Reference (Terraform)       │  │
│  │  ├── S3 Buckets (Backups)                        │  │
│  │  ├── DynamoDB (Rastreo)                         │  │
│  │  ├── CloudWatch (Monitoreo)                      │  │
│  │  └── SNS (Alertas)                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
proyecto-iot/
├── scripts/                          # Scripts Python
│   ├── generar_datos_iot.py          # Generador de datos sintéticos
│   ├── verificar_tamano_mongodb.py   # Verificación de tamaño
│   ├── verify_dr.py                  # Validación de Disaster Recovery
│   ├── generar_catalogo_datos.py      # Generador del catálogo de datos
│   └── etl_mongodb_bigquery.py        # ETL MongoDB a BigQuery
│
├── dashboard/                         # Dashboard de monitoreo
│   └── dashboard_monitoreo.py         # Generador de gráficos
│
├── terraform/                         # Infrastructure as Code
│   ├── providers.tf                   # Configuración de proveedores
│   ├── variables.tf                   # Variables de entrada
│   ├── main.tf                        # Recursos principales
│   ├── outputs.tf                     # Salidas de Terraform
│   └── terraform.tfvars.example       # Archivo de ejemplo
│
├── docs/                              # Documentación
│   ├── arquitectura.md                # Descripción de arquitectura
│   ├── disaster-recovery.md           # Plan de DR
│   └── README.md (este archivo)       # Guía principal
│
├── database/                          # Documentación de BD
│   ├── README.md                      # Notas de BD
│   └── scripts/                       # Scripts de BD
│
├── data/                              # Datos (generados localmente)
│
├── evidencias/                        # Evidencias de requisitos
│   ├── requisito-13/                  # Pruebas de 50 GB
│   ├── requisito-14/                  # Pruebas de DR
│   ├── requisito-15/                  # Pruebas de Dashboard
│   ├── requisito-16/                  # Pruebas de Terraform
│   └── requisito-17/                  # Catálogo de datos generado
│
├── .env.example                       # Plantilla de variables de entorno
├── .gitignore                         # Archivos ignorados por Git
├── requirements.txt                   # Dependencias Python
└── README.md                          # Este archivo
```

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias

#### Windows PowerShell

```powershell
# Clonar o descargar el proyecto
cd "c:\Users\Mai\Downloads\bd ejercicios"

# Crear entorno virtual
python -m venv venv

# Activar entorno
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python -c "import pymongo, pandas, matplotlib; print('✓ Todas las dependencias instaladas')"
```

### 2. Configuración de MongoDB

#### Opción A: MongoDB Atlas (Recomendado)

1. Crear cuenta gratuita en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crear un cluster
3. Obtener connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/iot_platform?retryWrites=true&w=majority
   ```

#### Opción B: MongoDB Local

```powershell
# Descargar e instalar MongoDB Community
# https://www.mongodb.com/try/download/community

# Iniciar servicio (PowerShell Admin)
net start MongoDB

# Verificar conexión
mongosh "mongodb://localhost:27017"
```

### 3. Configuración de Variables de Entorno

```powershell
# Copiar plantilla
Copy-Item .env.example .env

# Editar .env y configurar:
# MONGODB_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/iot_platform
# BIGQUERY_PROJECT_ID=tu-proyecto-google-cloud
# BIGQUERY_DATASET=iot_warehouse
# AWS_REGION=us-east-1
# AWS_DR_REGION=us-west-2
# AWS_PROFILE=default
```

### 4. Data Warehouse con BigQuery Sandbox

BigQuery separa las consultas analíticas (OLAP) del almacenamiento transaccional (OLTP) en MongoDB. El ETL aplana las colecciones `sensors` y `sensor_readings` en `dim_sensors` y `fact_readings`; cada ejecución reemplaza el contenido de ambas tablas para que la carga completa sea repetible.

1. Crea un proyecto en Google Cloud y habilita BigQuery Sandbox, que permite probar BigQuery sin añadir una tarjeta de crédito.
2. Instala las dependencias del proyecto: `pip install -r requirements.txt`.
3. Autentica Application Default Credentials con `gcloud auth application-default login`.
4. Completa `BIGQUERY_PROJECT_ID` en `.env`. `BIGQUERY_DATASET` y `BIGQUERY_LOCATION` son opcionales (por defecto `iot_warehouse` y `US`).
5. Ejecuta la carga desde la raíz del proyecto:

```powershell
python scripts/etl_mongodb_bigquery.py --batch-size 1000
```

Para probar con pocas filas por colección, usa `--limit 100`. Se requiere una conexión válida en `MONGODB_URI` y acceso de lectura a las colecciones configuradas. Las credenciales de Google se obtienen mediante ADC y no deben guardarse en `.env` ni en el repositorio.

### 5. Data Lake en Parquet (local o Amazon S3)

`scripts/data_lake_manager.py` exporta MongoDB por lotes y separa los datos en tres zonas: `raw` conserva cada documento como Extended JSON, `processed` aplana sensores y lecturas, y `curated` resume las lecturas por día y tipo de sensor. El destino predeterminado es `data_lake/` en disco; BigQuery sigue siendo un flujo independiente.

```powershell
# Prueba local limitada
python scripts/data_lake_manager.py --limit 100

# Exportación a un bucket S3 existente
python scripts/data_lake_manager.py --storage s3 --limit 100
```

Para S3, configura `AWS_DATA_LAKE_BUCKET`, `AWS_REGION` y, si corresponde, `AWS_PROFILE` en `.env`. El perfil/entorno AWS debe tener permiso `s3:PutObject` sobre el bucket; el script no crea buckets ni configura credenciales. `AWS_DATA_LAKE_PREFIX` define el prefijo (por defecto `iot-data`). Requiere `pyarrow`, incluido en `requirements.txt`. Prueba primero con `--limit`; no es necesario generar ni subir 50 GB para validar la arquitectura.

### 6. CI/CD con GitHub Actions

El workflow `.github/workflows/deploy.yml` se ejecuta en cada `push`, `pull_request` y también puede iniciarse manualmente desde la pestaña **Actions**. Siempre compila y prueba Python y valida Terraform. Al habilitar `TERRAFORM_PLAN_ENABLED`, además ejecuta `terraform plan` en cada `push`. En la rama predeterminada, `terraform apply` se habilita por separado con `TERRAFORM_APPLY_ENABLED` y requiere aprobación del environment de GitHub `production`.

Antes de habilitar plan/apply:

1. Crea un bucket S3 privado para el estado de Terraform, con versionado y cifrado. El rol de CI necesita acceso al bucket y a los objetos del estado y del archivo `.tflock`.
2. Configura AWS OIDC para GitHub Actions y crea un rol IAM de permisos mínimos. Limita la confianza del rol a este repositorio y a la rama que despliega; no uses claves AWS de larga duración.
3. En **Settings → Secrets and variables → Actions → Variables**, define `AWS_ROLE_ARN`, `AWS_REGION`, `TF_STATE_BUCKET`, `TF_STATE_KEY` (por ejemplo, `iot-platform/terraform.tfstate`) y `ATLAS_PROJECT_ID`.
4. En **Secrets**, define `ATLAS_PUBLIC_KEY` y `ATLAS_PRIVATE_KEY` para MongoDB Atlas.
5. Crea el environment `production` y configura revisores requeridos. Luego define `TERRAFORM_PLAN_ENABLED=true`; tras revisar que el plan sea correcto, define `TERRAFORM_APPLY_ENABLED=true` para habilitar despliegues en la rama predeterminada.

El job de plan publica el archivo binario `tfplan` como artefacto privado de Actions durante un día; el job de apply descarga y aplica exactamente ese plan, después de la aprobación del environment. Los archivos de plan pueden contener valores sensibles: limita el acceso al repositorio y a sus ejecuciones de Actions. Los pull requests solo ejecutan las comprobaciones sin credenciales cloud. Si ya gestionaste infraestructura con un estado local, migra ese estado al backend S3 antes de activar el plan; no inicialices el CI con un estado vacío para recursos que ya existen. No guardes credenciales ni `terraform.tfvars` en el repositorio.

### 7. Generar Datos IoT (Pequeño Volumen - Prueba)

```powershell
# Generar 10,000 documentos para prueba
python scripts/generar_datos_iot.py `
  --num-sensors 100 `
  --total-documents 10000 `
  --batch-size 1000

# Esperado: ~10-15 segundos
```

### 6. Verificar Tamaño

```powershell
# Ver estadísticas
python scripts/verificar_tamano_mongodb.py

# Esperado: ~50-100 MB
```

### 7. Generar Dashboard

```powershell
# Generar gráficos
python dashboard/dashboard_monitoreo.py

# Salida: dashboard_iot_monitoreo.png en el directorio dashboard/
```

### 8. Validar Disaster Recovery

```powershell
# Verificación completa
python scripts/verify_dr.py --full

# O comprobaciones específicas
python scripts/verify_dr.py --check-config
python scripts/verify_dr.py --check-mongodb
```

### 9. Preparar Terraform

```powershell
# Cambiar a directorio Terraform
cd terraform

# Copiar archivo de ejemplo
Copy-Item terraform.tfvars.example terraform.tfvars

# Editar terraform.tfvars con tus valores
notepad terraform.tfvars

# Validar configuración (sin crear recursos)
terraform init
terraform validate
terraform fmt -check

# Ver plan (ANTES de aplicar)
terraform plan
```

## 📊 Escalamiento a 50 GB

Para alcanzar el objetivo de 50 GB:

### Opción 1: Generación Incremental (Recomendada)

```powershell
# Fase 1: 100,000 documentos (< 1 minuto)
python scripts/generar_datos_iot.py --total-documents 100000

# Fase 2: 1 millón de documentos (10-15 minutos)
python scripts/generar_datos_iot.py --total-documents 1000000

# Fase 3: 5 millones de documentos (1-2 horas)
python scripts/generar_datos_iot.py --total-documents 5000000

# Fase 4: 16+ millones de documentos (10-14 horas)
python scripts/generar_datos_iot.py --total-documents 16000000
```

### Opción 2: Con Configuración Avanzada

```powershell
# Generar con más sensores y datos
python scripts/generar_datos_iot.py `
  --num-sensors 5000 `
  --total-documents 16000000 `
  --batch-size 1000 `
  --target-gb 50
```

### Verificación de Progreso

```powershell
# Verificar en cualquier momento (sin interrumpir generación)
python scripts/verificar_tamano_mongodb.py

# Debería mostrar progreso incremental hacia 50 GB
```

## 🔐 Configuración de AWS

### Requisitos Previos

1. **Cuenta AWS activa** con permisos administrativos
2. **AWS CLI** instalado y configurado
3. **Terraform** 1.0+ instalado

### Configuración de Credenciales

```powershell
# Instalar AWS CLI
pip install awscli

# Configurar credenciales
aws configure --profile default

# Se pedirá:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json

# Verificar configuración
aws sts get-caller-identity
```

### Desplegar Infraestructura (Opcional)

```powershell
cd terraform

# Inicializar Terraform
terraform init

# Ver qué se va a crear (SIN crear todavía)
terraform plan

# SI TODO SE VE BIEN, crear recursos
# IMPORTANTE: Esto puede generar costos
terraform apply

# Verificar salidas
terraform output
```

## 📈 Monitoreo Continuo

```powershell
# Ejecutar verificación cada hora (PowerShell)
while ($true) {
    Write-Host "$(Get-Date) - Verificando..."
    python scripts/verificar_tamano_mongodb.py
    Start-Sleep -Seconds 3600  # Esperar 1 hora
}
```

## 🔍 Diagnóstico de Problemas

### Conexión a MongoDB Fallida

```powershell
# Verificar MONGODB_URI
cat .env

# Testear conexión
python -c "
from pymongo import MongoClient
import os
uri = os.getenv('MONGODB_URI')
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✓ Conexión OK')
except Exception as e:
    print(f'✗ Error: {e}')
"

# Verificar firewall (si es local)
# Verificar credenciales (si es Atlas)
```

### Scripts No Se Ejecutan

```powershell
# Verificar Python
python --version

# Verificar entorno virtual
.\venv\Scripts\Activate.ps1

# Verificar dependencias
pip list | grep pymongo

# Reinstalar si es necesario
pip install --upgrade -r requirements.txt
```

### Dashboard No Genera Gráficos

```powershell
# Verificar que hay datos
python scripts/verificar_tamano_mongodb.py

# Si hay datos pero no gráficos:
# - Necesita matplotlib (instalado con requirements.txt)
# - Necesita al menos 1000 documentos para gráficos significativos

# Probar manualmente
python -c "
import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
plt.savefig('test.png')
print('✓ Matplotlib funciona')
"
```

## 📝 Documentación Detallada

- **[docs/arquitectura.md](docs/arquitectura.md)**: Descripción de componentes
- **[docs/disaster-recovery.md](docs/disaster-recovery.md)**: Plan de DR completo
- **Scripts**: Cada script tiene docstrings detallados

## 🎯 Cumplimiento de Requisitos

### Requisito 13: 50 GB de Datos IoT

**Evidencia**:
```powershell
# Ejecutar verificación
python scripts/verificar_tamano_mongodb.py

# Guardar salida
python scripts/verificar_tamano_mongodb.py > evidencias/requisito-13/resultado.txt

# Dashboard
python dashboard/dashboard_monitoreo.py
# Buscar "Progreso hacia 50GB"
```

**Archivo**: `evidencias/requisito-13/README.md`

### Requisito 14: Disaster Recovery

**Evidencia**:
```powershell
# Ejecutar validación
python scripts/verify_dr.py --full > evidencias/requisito-14/resultado.txt

# Captura manual:
# 1. MongoDB Atlas Console → Deployment → Replication
# 2. AWS Console → S3 → Buckets
# 3. Backup completado exitosamente
```

**Archivo**: `docs/disaster-recovery.md` + `evidencias/requisito-14/README.md`

### Requisito 15: Dashboard

**Evidencia**:
```powershell
# Generar dashboard
python dashboard/dashboard_monitoreo.py

# Guardar captura
# dashboard_iot_monitoreo.png en dashboard/
# Copiar a evidencias/
Copy-Item dashboard/dashboard_iot_monitoreo.png evidencias/requisito-15/
```

**Archivo**: `evidencias/requisito-15/dashboard_iot_monitoreo.png`

### Requisito 16: Terraform

**Evidencia**:
```powershell
cd terraform

# Validar
terraform validate > ..\evidencias\requisito-16\validate.txt

# Plan (sin aplicar)
terraform plan > ..\evidencias\requisito-16\plan.txt

# Mostrar estructura
terraform fmt -check
```

**Archivo**: `evidencias/requisito-16/plan.txt` + archivos .tf

## 📋 Checklist de Implementación

- [x] Estructura de proyecto creada
- [x] Dependencias documentadas (requirements.txt)
- [x] Scripts de generación de datos
- [x] Verificación de tamaño
- [x] Dashboard de monitoreo
- [x] Validación de Disaster Recovery
- [x] Infraestructura Terraform
- [x] Documentación completa
- [ ] Datos escalados a 50 GB (requiere tiempo)
- [ ] AWS configurado (requiere credenciales)
- [ ] Evidencias capturadas
- [ ] Validación final completada

## 🔒 Seguridad

### NO hacer:

❌ No commits contraseñas en repositorio
❌ No escribir credenciales en código
❌ No compartir .env en público

### Hacer:

✅ Usar .env.example como plantilla
✅ Mantener .env en .gitignore
✅ Usar variables de entorno
✅ Credenciales solo en máquina local
✅ Revisar antes de commitear

## 📞 Soporte

Para problemas específicos:

1. **Generación de datos**: Ver `scripts/generar_datos_iot.py` docstring
2. **MongoDB**: Consultar [MongoDB Documentation](https://docs.mongodb.com/)
3. **AWS**: Consultar [AWS Documentation](https://docs.aws.amazon.com/)
4. **Terraform**: Consultar [Terraform Documentation](https://www.terraform.io/docs)

## 📄 Licencia

Proyecto académico. Uso libre para fines educativos.

## ✍️ Autor

Desarrollo académico de IoT Platform.

---

**Última actualización**: 2024
**Estado**: En desarrollo
**Versión**: 1.0
