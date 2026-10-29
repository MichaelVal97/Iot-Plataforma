# Disaster Recovery - IoT Platform

## Descripción General

Este documento describe la estrategia de Disaster Recovery (DR) para IoT Platform, incluyendo:
- Arquitectura de recuperación
- Procedimientos de failover
- Validación de recuperación
- Objetivos de RPO y RTO

## Arquitectura de Disaster Recovery

### Regiones AWS

| Aspecto | Primaria | Secundaria (DR) |
|---------|----------|-----------------|
| Región AWS | `us-east-1` | `us-west-2` |
| Disponibilidad | Multi-AZ | Multi-AZ |
| Latencia | Baseline | ~50 ms |
| Distancia | Este de EE.UU. | Oeste de EE.UU. |

### Topología de MongoDB

```
┌─────────────────────────────────────┐
│     MongoDB Atlas Replica Set       │
├─────────────────────────────────────┤
│                                     │
│  Primaria (us-east-1)               │
│  ├── Nodo 1 (Primario)             │
│  ├── Nodo 2 (Secundario)           │
│  └── Nodo 3 (Secundario)           │
│                                     │
│  Replicación Automática             │
│       (< 1 segundo)                 │
│            ↓                        │
│  Secundaria (us-west-2)             │
│  ├── Nodo 4 (Secundario)           │
│  └── Nodo 5 (Secundario)           │
│                                     │
│  Failover Automático                │
│  (en caso de fallo primario)        │
│                                     │
└─────────────────────────────────────┘
```

## Objetivos de Recuperación

### RPO (Recovery Point Objective)
- **Objetivo**: 60 minutos
- **Significado**: Máximo 60 minutos de pérdida de datos
- **Realidad**: MongoDB Atlas replicación ≈ < 1 segundo
- **Garantía**: Casi cero pérdida de datos

### RTO (Recovery Time Objective)
- **Objetivo**: 15 minutos
- **Significado**: Máximo 15 minutos para recuperación completa
- **Realidad**: Failover automático ≈ 10-30 segundos
- **Garantía**: Recuperación muy rápida automática

## Componentes de DR

### 1. Replicación de Datos (MongoDB)

**Tipo**: Replicación nativa de MongoDB

**Configuración**:
- Replica Set con 3+ nodos
- Distribuido entre 2 regiones
- Replicación síncrona con `writeConcern: "majority"`

**Validación**:
```javascript
// En MongoDB Shell
rs.status()

// Buscar replicationLag
{
  "members": [
    {
      "name": "primary-us-east-1:27017",
      "state": 1,  // 1 = PRIMARY
      "optime": {...}
    },
    {
      "name": "secondary-us-west-2:27017",
      "state": 2,  // 2 = SECONDARY
      "optimeDate": {...},
      "replicationLag": 0  // Debería ser < 1 segundo
    }
  ]
}
```

### 2. Backups Automáticos

**Proveedor**: MongoDB Atlas

**Configuración**:
- Backups automáticos cada 6 horas
- Retención mínima: 7 días
- Copias en ambas regiones

**Ubicación**:
- Almacenados en S3 (configurado en Terraform)
- Cross-region replication habilitada
- Encriptación en reposo

**Validación en MongoDB Atlas Console**:
1. Deployment → Backup
2. Verificar "Backup enabled"
3. Ver historial de backups completados
4. Verificar "Restore from Backup" disponible

### 3. Failover Automático

**Mecanismo**: MongoDB Replica Set failover

**Proceso**:
1. Pérdida de conexión con primario
2. Secundarios detectan en ~5 segundos
3. Elección de nuevo primario (10-30 segundos)
4. Redireccionamiento automático de conexiones

**Ventajas**:
- Totalmente automático
- Sin intervención manual
- Detecta fallos de red, hardware o software

**Validación**: Prueba de failover en MongoDB Atlas Console

### 4. Backups en AWS (S3)

**Archivos Terraform**: `terraform/main.tf`

**Recursos**:
- Bucket S3 primario: `iot-platform-backups-primary-{ACCOUNT_ID}`
- Bucket S3 DR: `iot-platform-backups-dr-{ACCOUNT_ID}`
- Replicación S3: Primario → DR
- Lifecycle: Transición a Glacier después de 30 días

**RTC (Replication Time Control)**:
- Objetivo: 15 minutos
- Métrica: `ReplicationLatency`

### 5. Monitoreo y Alertas

**CloudWatch**:
- Log Group: `/aws/iot-platform/iot-platform`
- Retención: 30 días
- Alarms para fallos de backup

**SNS**:
- Topic: `iot-platform-alerts`
- Notificaciones por fallos críticos

**Verificación**: `scripts/verify_dr.py`

## Procedimiento de Recuperación

### Escenario 1: Fallo de Base de Datos (Automático)

**Situación**: Primaria en us-east-1 no responde

**Pasos**:
1. MongoDB detecta fallo (~5 segundos)
2. Elige secundaria como nuevo primario (~10-30 segundos)
3. Aplicación se reconecta automáticamente
4. Servicio continúa sin intervención

**Verificación**:
```bash
# Conectar desde región DR
mongosh "mongodb+srv://cluster.mongodb.net/iot_platform"

# Verificar que es primaria
db.rs.status()

# Verificar datos
db.sensor_readings.count()
```

**Tiempo total**: 10-60 segundos

### Escenario 2: Pérdida de Región (Manual)

**Situación**: Toda la región primaria (us-east-1) no disponible

**Pasos**:

#### Fase 1: Detección (10 minutos)
1. Monitoreo detecta fallo múltiple
2. SNS envía alertas
3. Equipo es notificado

#### Fase 2: Failover (5-10 minutos)
1. Acceder a MongoDB Atlas Console
2. Deployment → Overview
3. Click "Initiate High Availability Failover"
4. Seleccionar región us-west-2 como primaria
5. Confirmar failover

#### Fase 3: Redireccionamiento (5 minutos)
1. Actualizar MONGODB_URI en aplicación para us-west-2
2. O dejar Replica Set SRV DNS (hace automático)
3. Reiniciar aplicación si es necesario

#### Fase 4: Validación (5 minutos)
```bash
# Conectar a aplicación
python scripts/verificar_tamano_mongodb.py

# Verificar datos
# Debería tener todos los documentos

# Verificar escrituras
python scripts/generar_datos_iot.py --total-documents 100 --num-sensors 10
```

**Tiempo total**: 15-30 minutos

### Escenario 3: Restauración desde Backup

**Situación**: Corrupción de datos detectada

**Pasos**:

#### En MongoDB Atlas Console:
1. Deployment → Backup
2. Seleccionar punto de restauración
3. Click "Restore"
4. Seleccionar:
   - Opción: "Restore to Existing Cluster"
   - Cluster: tu cluster actual
   - Punto de tiempo: Selecciona backup válido
5. Confirmar

**Validación**:
```bash
# Esperar completación (5-30 minutos según tamaño)
python scripts/verificar_tamano_mongodb.py

# Verificar integridad de datos
db.sensor_readings.findOne()
db.sensors.findOne()

# Comparar con última verificación conocida
```

**Tiempo total**: 30-60 minutos

## Validación de Disaster Recovery

### Verificación Automática

Ejecutar el script de validación:

```bash
# Verificación completa
python scripts/verify_dr.py --full

# Verificación específica
python scripts/verify_dr.py --check-mongodb
python scripts/verify_dr.py --check-aws
python scripts/verify_dr.py --check-config
```

**Qué verifica**:
- Archivos de configuración existen
- Variables de entorno configuradas
- Conectividad a MongoDB
- Credenciales AWS disponibles
- Configuración Terraform válida

### Verificación Manual

#### 1. Replicación en MongoDB Atlas (5 minutos)

```
Pasos:
1. Acceder a https://cloud.mongodb.com
2. Deployment → Replication
3. Verificar:
   ✓ Hay 3+ nodos
   ✓ Distribuidos entre regiones
   ✓ "Replication Lag" < 1 segundo
```

#### 2. Backups en MongoDB Atlas (5 minutos)

```
Pasos:
1. Deployment → Backup
2. Verificar:
   ✓ Backup automático HABILITADO
   ✓ Hay backups completados
   ✓ Retención ≥ 7 días
   ✓ "Last backup" es reciente
3. Click "Restore" para verificar disponibilidad
```

#### 3. Buckets S3 (5 minutos)

```
En AWS Console (us-east-1):
1. S3 → Buckets
2. Buscar "iot-platform-backups-primary-*"
3. Verificar:
   ✓ Bucket existe
   ✓ Tiene objetos
   ✓ Versioning habilitado

En AWS Console (us-west-2):
1. S3 → Buckets
2. Buscar "iot-platform-backups-dr-*"
3. Verificar:
   ✓ Bucket existe
   ✓ Tiene objetos (copia de primario)
```

#### 4. Failover de Prueba (10 minutos)

```
1. MongoDB Atlas Console
2. Deployment → Overview
3. Click "Test Failover"
4. Observar:
   ✓ Fallo ocurre
   ✓ Nuevo primario se elige
   ✓ Cluster vuelve a normal en < 2 minutos
   ✓ NO hay pérdida de datos
```

#### 5. Prueba de Restauración (15 minutos)

```
1. MongoDB Atlas Console
2. Deployment → Backup
3. Seleccionar backup de hace 1-2 horas
4. Click "Restore"
5. Seleccionar "Restore to Existing Cluster"
6. Esperar completación
7. Verificar:
   ✓ Datos son accesibles
   ✓ Cantidad de documentos correcta
   python scripts/verificar_tamano_mongodb.py
```

## Checklist de Validación

- [ ] MongoDB Atlas está configurado con Multi-Region
- [ ] Replicación Lag < 1 segundo en Deployment → Replication
- [ ] Backups están habilitados y tienen historial
- [ ] S3 buckets existen en ambas regiones
- [ ] Replicación S3 está habilitada
- [ ] Terraform puede validarse sin errores: `terraform validate`
- [ ] `scripts/verify_dr.py` pasa todas las comprobaciones
- [ ] Failover de prueba completado exitosamente
- [ ] Restauración desde backup probada
- [ ] Documentación de procedimientos revisada

## Matriz de Responsabilidades

| Tarea | Responsable | Frecuencia |
|-------|-------------|-----------|
| Verificar replicación | DevOps | Diaria |
| Revisar backups | DBA | Diaria |
| Validar scripts | Dev | Semanal |
| Prueba de failover | Ops | Mensual |
| Prueba de restauración | Ops | Trimestral |
| Revisión de documentación | Tech Lead | Anual |

## Consideraciones de Costos

### MongoDB Atlas
- Multi-Region Replication: Incluido en Dedicated tiers
- Shared tier: Verificar plan

### AWS
- S3 Backups: ~$0.023/GB/mes
- Cross-region replication: ~$0.02/GB replicado
- CloudWatch Logs: ~$0.50/GB
- SNS: ~$0.50 por millón de notificaciones

**Total estimado**: $20-50/mes

## Mejoras Futuras

1. **Automatización de validación**: Cronograma diario de verificaciones
2. **Runbook automático**: Scripts que ejecuten failover con confirmación
3. **Capacitación del equipo**: Simulacros de DR regulares
4. **Documentación de lecciones aprendidas**: Registro de incidentes
5. **Monitoreo de RPO/RTO**: Dashboard de cumplimiento

## Referencias

- [MongoDB Replica Set Documentation](https://docs.mongodb.com/manual/replication/)
- [MongoDB Atlas Backup Documentation](https://docs.mongodb.com/atlas/backup/)
- [AWS S3 Cross-Region Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
