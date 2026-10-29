# Arquitectura de IoT Platform

## Descripción General

IoT Platform es una solución académica de Internet de las Cosas (IoT) basada en MongoDB, diseñada para cumplir los requisitos 13-16 de la rúbrica:

- **Requisito 13**: Almacenamiento de 50+ GB de datos IoT
- **Requisito 14**: Disaster Recovery multi-región
- **Requisito 15**: Dashboard de monitoreo
- **Requisito 16**: Infrastructure as Code con Terraform

## Componentes Principales

### 1. Base de Datos: MongoDB Atlas

- **Ubicación**: Nube (MongoDB Atlas)
- **Regiones**: 
  - Primaria: `us-east-1`
  - Secundaria (DR): `us-west-2`
- **Colecciones**:
  - `sensor_readings`: Datos de sensores (~1,000 documentos/sensor/día)
  - `sensors`: Metadatos de sensores

### 2. Data Warehouse: Google BigQuery

- **Rol**: Capa analítica OLAP separada de MongoDB Atlas, que conserva la escritura transaccional OLTP.
- **Dataset**: `iot_warehouse` (configurable mediante `BIGQUERY_DATASET`).
- **Modelo dimensional**:
     - `dim_sensors`: metadatos y ubicación de cada sensor.
     - `fact_readings`: medidas de cada lectura, relacionadas mediante `sensor_id`.
- **ETL**: `scripts/etl_mongodb_bigquery.py` extrae ambas colecciones desde Atlas, aplana los campos anidados y carga BigQuery por lotes.
- **Ejecución**: carga completa; reemplaza las dos tablas en cada ejecución para evitar duplicados. Usa BigQuery Sandbox y Application Default Credentials.

### 3. Generación de Datos

**Script**: `scripts/generar_datos_iot.py`

Genera datos sintéticos realistas con:
- 100-1000 sensores simulados
- Múltiples tipos de sensores (weather, air_quality, energy, motion, etc.)
- Datos históricos de 365 días
- Inserción por lotes para evitar problemas de RAM
- Soporte para reanudación de interrupciones

**Modelo de datos**:

```json
{
  "sensor_id": "sensor_000001",
  "timestamp": "2024-01-15T14:30:45Z",
  "tipo_sensor": "weather",
  "temperatura": 24.5,
  "humedad": 72.1,
  "presion": 1012.4,
  "calidad_aire": 42,
  "energia": 0.81,
  "estado": "normal",
  "ubicacion": {
    "lat": 40.7128,
    "lon": -74.0060,
    "ciudad": "Nueva York",
    "pais": "Estados Unidos"
  },
  "datos_adicionales": {
    "velocidad_viento": 12.5,
    "radiacion_solar": 450,
    "precipitacion": 0
  },
  "confiabilidad": 0.95
}
```

### 4. Verificación de Tamaño

**Script**: `scripts/verificar_tamano_mongodb.py`

Reporta:
- Cantidad de documentos
- Tamaño lógico de datos
- Tamaño de índices
- Tamaño total de almacenamiento
- Porcentaje respecto a objetivo de 50 GB
- Diferencias entre tamaño físico y lógico

### 5. Dashboard de Monitoreo

**Script**: `dashboard/dashboard_monitoreo.py`

Genera gráficos con:
- Estadísticas generales (documentos, sensores, almacenamiento)
- Distribución de estados
- Sensores activos vs inactivos
- Progreso hacia objetivo de 50 GB
- Rangos de temperatura y humedad
- Series de tiempo de registros
- Trayectorias de temperatura y humedad

**Salida**: PNG de alta resolución (150 DPI)

### 6. Disaster Recovery

**Documentación**: `docs/disaster-recovery.md`

Arquitectura de DR:
- Replicación automática entre regiones (MongoDB Atlas)
- Backups automáticos y cross-region
- RPO: 60 minutos
- RTO: 15 minutos
- Validación mediante `scripts/verify_dr.py`

### 7. Infrastructure as Code

**Directorio**: `terraform/`

Recursos AWS:
- S3 buckets para backups (primaria + DR)
- Replicación S3 entre regiones
- DynamoDB table para rastreo de backups
- CloudWatch Logs y Alarms
- SNS Topics para notificaciones
- IAM Roles y Policies

**No genera costos innecesarios**:
- Recursos opcionales (S3, DynamoDB) deshabilitados por defecto
- CloudWatch gratuito hasta ciertos límites
- MongoDB Atlas maneja su propia replicación

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                      IoT Platform Flow                          │
└─────────────────────────────────────────────────────────────────┘

1. GENERACIÓN DE DATOS
   generar_datos_iot.py
        ↓
   Genera documentos realistas
        ↓
   Inserta en lotes en MongoDB
        ↓
   
2. ALMACENAMIENTO
   MongoDB Atlas (Región Primaria: us-east-1)
        ↓
   Replicación automática a Secundaria (us-west-2)
        ↓
   Backups diarios en S3
        ↓

3. DATA WAREHOUSE (OLAP)
   scripts/etl_mongodb_bigquery.py
        ↓ extrae sensor_readings y sensors por lotes
   BigQuery Sandbox: dim_sensors + fact_readings
        ↓ análisis SQL sin cargar consultas analíticas en MongoDB

4. VERIFICACIÓN DE TAMAÑO
   verificar_tamano_mongodb.py
        ↓
   Consulta dbStats y collStats
        ↓
   Reporta progreso vs 50 GB
        ↓

5. MONITOREO
   dashboard_monitoreo.py
        ↓
   Consulta agregaciones en MongoDB
        ↓
   Genera gráficos con Matplotlib
        ↓
   Exporta PNG
        ↓

6. DISASTER RECOVERY
   verify_dr.py
        ↓
   Verifica configuración
        ↓
   Proporciona guía de validación manual
        ↓

7. INFRAESTRUCTURA
   terraform/
        ↓
   Provisiona recursos AWS
        ↓
   Configura backups y replicación
        ↓
   Habilita monitoreo y alertas
```

## Índices de Base de Datos

### Colección: sensor_readings

```javascript
// Índice compuesto para consultas por sensor y tiempo
db.sensor_readings.createIndex({ sensor_id: 1, timestamp: 1 })

// Índice en timestamp para ordenamiento rápido
db.sensor_readings.createIndex({ timestamp: 1 })

// Índice en tipo_sensor para filtrado
db.sensor_readings.createIndex({ tipo_sensor: 1 })

// Índice en sensor_id para búsquedas
db.sensor_readings.createIndex({ sensor_id: 1 })
```

**Impacto**: ~15-20% overhead de almacenamiento

### Colección: sensors

```javascript
// Índice en sensor_id (clave primaria)
db.sensors.createIndex({ sensor_id: 1 }, { unique: true })

// Índice en tipo_sensor
db.sensors.createIndex({ tipo_sensor: 1 })
```

## Escalabilidad

### Volumen de Datos Actual
- ~100 sensores
- ~1,000 documentos/sensor/día
- ~100,000 documentos iniciales
- ~400 MB a 1 GB iniciales

### Escalamiento a 50 GB

**Estrategia**:
1. Aumentar cantidad de sensores: 100 → 10,000
2. Aumentar documentos por sensor: 1,000/día → 10,000/día
3. Extender período histórico: 365 días → 730+ días

**Tiempo estimado**:
- ~1 documento ≈ 2-5 KB
- 50 GB ÷ 3 KB/doc ≈ 16.7 millones documentos
- Con inserción de 1,000 docs/batch: ~16,700 lotes
- A 2-5 segundos/lote: 10-14 horas en total

**Comando de generación escalado**:
```bash
python scripts/generar_datos_iot.py \
  --num-sensors 10000 \
  --total-documents 16000000 \
  --batch-size 1000 \
  --target-gb 50
```

## Consideraciones de Costos

### MongoDB Atlas
- Free tier: 512 MB de almacenamiento
- Shared tier: Variable según uso
- Dedicated tier: Desde ~$57/mes

### AWS Resources (Terraform)
- S3 Backups: ~$0.023/GB/mes
- DynamoDB: Gratuito (PAY_PER_REQUEST bajo uso)
- CloudWatch: Gratuito hasta 5 GB logs/mes
- Cross-region replication: ~$0.02/GB replicado

**Total estimado**: $50-150/mes para producción

### BigQuery Sandbox
- Sandbox gratuito para pruebas y consultas analíticas, sujeto a cuotas y límites de Google Cloud.
- No requiere añadir una tarjeta de crédito para usar el Sandbox.
- Este proyecto carga los datos mediante jobs por lotes; no usa streaming.
- En producción, revisar precios de almacenamiento y consultas de BigQuery antes de salir del Sandbox.

## Seguridad

### Credenciales
- Ninguna credencial en código
- Usar variables de entorno
- `.env.example` como plantilla
- `.env` en `.gitignore`

### Conexión MongoDB
- Usar MONGODB_URI con autenticación
- Habilitar TLS/SSL en Atlas
- Restringir acceso por IP

### AWS
- Usar perfiles IAM
- Roles con permisos mínimos
- Cifrado en reposo y tránsito

## Limitaciones Conocidas

1. **Datos sintéticos**: Realistas pero no reales
2. **Escala de DR**: Validación manual necesaria
3. **Costos AWS**: Pueden variar según uso
4. **MongoDB Atlas**: Requiere cuenta (plan gratuito disponible)
5. **Dashboard**: Requiere 1000+ documentos para gráficos significativos

## Próximos Pasos

1. Configurar MongoDB Atlas
2. Instalar dependencias Python
3. Generar datos iniciales
4. Ejecutar dashboard
5. Validar Disaster Recovery
6. Provisionar infraestructura AWS
7. Generar evidencias
