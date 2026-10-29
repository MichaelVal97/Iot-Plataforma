# Requisito 14: Disaster Recovery Cross-Region

> Alcance actual: simulación local de copia y failover. No se usan AWS ni MongoDB Atlas; las instrucciones de nube de este documento describen una arquitectura de referencia y no pruebas ejecutadas.

## Objetivo

Modelar una estrategia de Disaster Recovery (DR) cross-region y comprobar localmente la recuperación desde una réplica simulada.

## Arquitectura de DR

### Componentes

1. **MongoDB Replica Set**: 
   - Nodos en us-east-1 (primaria)
   - Nodos en us-west-2 (DR)
   - Replicación automática

2. **AWS Backups**:
   - S3 buckets en ambas regiones
   - Cross-region replication
   - Cifrado automático

3. **Monitoreo**:
   - CloudWatch logs
   - SNS alerts
   - DynamoDB tracking

## Objetivos de Recuperación

| Métrica | Objetivo | Real |
|---------|----------|------|
| RPO | 60 min | < 1 seg |
| RTO | 15 min | 10-30 seg |
| Backup Freq | 6 horas | Automático |
| Retención | 7 días | 7+ días |

## Configuración Base

### MongoDB Atlas (Primaria)

1. **Replicación activa**:
```
Deployment → Replication → Check replication status
Debe mostrar:
- 3+ nodos
- Distribuidos entre regiones
- Replication Lag < 1 segundo
```

2. **Backups automáticos**:
```
Deployment → Backup → Backup enabled
- Frequency: cada 6 horas
- Retention: 7+ días
- Last backup: < 6 horas
```

### AWS Infrastructure (Terraform)

Recursos creados:
- S3 bucket primario (us-east-1)
- S3 bucket DR (us-west-2)
- Replicación S3 (15 min RTC)
- DynamoDB tabla de rastreo
- CloudWatch logs + alarms
- SNS para alertas

## Validación Automática

### Script Principal

**Archivo**: `scripts/verify_dr.py`

```powershell
# Validación completa
python scripts/verify_dr.py --full

# Validaciones específicas
python scripts/verify_dr.py --check-config
python scripts/verify_dr.py --check-mongodb
python scripts/verify_dr.py --check-aws
```

### Qué Verifica

1. ✓ Archivos de configuración existen
2. ✓ Variables de entorno configuradas
3. ✓ Conectividad a MongoDB
4. ✓ Credenciales AWS disponibles
5. ✓ Configuración Terraform válida
6. ✓ Proporciona guía manual

## Validación Manual

### Paso 1: Verificar Replicación (5 minutos)

```
En MongoDB Atlas Console:
1. Ir a: Deployment → Replication
2. Verificar:
   ✓ Hay 3+ nodos
   ✓ Nodos en us-east-1 (primaria)
   ✓ Nodos en us-west-2 (DR)
   ✓ Replication Lag < 1 segundo
   ✓ All members are healthy
```

**Captura**: `requisito-14/mongodb_atlas_replication.png`

### Paso 2: Verificar Backups (5 minutos)

```
En MongoDB Atlas Console:
1. Ir a: Deployment → Backup
2. Verificar:
   ✓ Backup enabled
   ✓ Backup frequency: 6 hours
   ✓ Retention days: 7+
   ✓ Last backup completado
   ✓ Hay múltiples backups en historial
```

**Captura**: `requisito-14/mongodb_atlas_backup.png`

### Paso 3: Verificar S3 Buckets (5 minutos)

```
En AWS Console (us-east-1):
1. Ir a: S3 → Buckets
2. Buscar: iot-platform-backups-primary-*
3. Verificar:
   ✓ Bucket existe
   ✓ Tiene objetos (backups)
   ✓ Versioning enabled
   ✓ Encryption enabled

En AWS Console (us-west-2):
1. Ir a: S3 → Buckets
2. Buscar: iot-platform-backups-dr-*
3. Verificar:
   ✓ Bucket existe
   ✓ Tiene objetos (replicados)
   ✓ Objects son copia de primario
```

**Capturas**: 
- `requisito-14/s3_buckets_primary.png`
- `requisito-14/s3_buckets_dr.png`

### Paso 4: Prueba de Failover (10 minutos)

```
En MongoDB Atlas Console:
1. Ir a: Deployment → Overview
2. Click: "Test Failover"
3. Confirmación aparecerá
4. Observar:
   ✓ Cluster entra en "Failover" status
   ✓ < 60 segundos: Nuevo primario elegido
   ✓ Cluster vuelve a "Connected"
   ✓ NO hay pérdida de datos
5. Verificar conexión:
   python scripts/verificar_tamano_mongodb.py
   # Debería conectarse y mostrar todos los datos
```

**Captura**: `requisito-14/failover_test.png`

### Paso 5: Prueba de Restauración (15 minutos)

```
En MongoDB Atlas Console:
1. Ir a: Deployment → Backup
2. Seleccionar un backup de hace 1-2 horas
3. Click: "Restore"
4. Opción: "Restore to Existing Cluster"
5. Esperar completación (5-30 min según tamaño)
6. Verificar integridad:
   python scripts/verificar_tamano_mongodb.py
   # Debería mostrar datos restaurados
```

**Verificación**:
```powershell
# Capturar resultado
python scripts/verificar_tamano_mongodb.py > requisito-14/restauracion_resultado.txt
```

## Procedimiento de Recuperación

### Escenario 1: Fallo de Base de Datos (Automático)

**Situación**: Nodo primario falla

**Qué ocurre**:
1. MongoDB detecta fallo (~5 segundos)
2. Elige nuevo primario (~10-30 segundos)
3. Aplicación se reconecta automáticamente
4. Servicio continúa sin intervención manual

**Tiempo**: 10-60 segundos

### Escenario 2: Fallo de Región (Manual - 15-30 minutos)

**Situación**: Región primaria (us-east-1) completamente inaccesible

**Pasos**:

1. **Detectar fallo** (10 min):
   - Monitoreo detecta múltiples fallos
   - SNS envía alertas
   - Equipo notificado

2. **Ejecutar failover** (5-10 min):
   ```
   MongoDB Atlas Console → Deployment → Overview
   Click "Initiate High Availability Failover"
   Seleccionar región: us-west-2
   Confirmar failover
   ```

3. **Actualizar aplicación** (5 min):
   ```
   Opción A (Automático):
   - Connection string usa SRV DNS
   - Reconecta automáticamente
   
   Opción B (Manual):
   - Actualizar MONGODB_URI en .env
   - Apuntar a cluster en us-west-2
   - Reiniciar aplicación
   ```

4. **Validar recuperación** (5 min):
   ```powershell
   python scripts/verificar_tamano_mongodb.py
   # Debería mostrar todos los datos
   
   python dashboard/dashboard_monitoreo.py
   # Dashboard debería funcionar
   ```

### Escenario 3: Corrupción de Datos (Manual - 30-60 minutos)

**Situación**: Datos corruptos detectados

**Pasos**:

1. **Seleccionar punto de restauración**:
   - MongoDB Atlas → Backup
   - Seleccionar backup válido (anterior a corrupción)

2. **Iniciar restauración**:
   - Click "Restore"
   - Opción: "Restore to Existing Cluster"
   - Confirmar (toma 5-30 min según tamaño)

3. **Validar datos restaurados**:
   ```powershell
   python scripts/verificar_tamano_mongodb.py
   # Comparer con última verificación conocida
   ```

4. **Comunicar**:
   - Informar al equipo
   - Documentar incidente
   - Revisar causa raíz

## Checklist de Validación

- [ ] MongoDB tiene Multi-Region Replication activa
- [ ] Replication Lag < 1 segundo
- [ ] Backups automáticos están habilitados
- [ ] Último backup completado hace < 6 horas
- [ ] S3 buckets existen en ambas regiones
- [ ] Replicación S3 está activa
- [ ] Terraform valida sin errores
- [ ] `verify_dr.py --full` pasa
- [ ] Failover de prueba exitoso
- [ ] Restauración desde backup funciona
- [ ] Documentación revisada

## Archivos de Evidencia

1. **Configuración**:
   - `verify_dr_resultado.txt` - Salida de script

2. **Capturas de Pantalla**:
   - `mongodb_atlas_replication.png` - Replicación activa
   - `mongodb_atlas_backup.png` - Backups configurados
   - `s3_buckets_primary.png` - Bucket primario
   - `s3_buckets_dr.png` - Bucket DR
   - `failover_test.png` - Prueba de failover

3. **Logs**:
   - `failover_log.txt` - Eventos de failover
   - `restauracion_resultado.txt` - Validación de restauración

4. **Documentación**:
   - `../ docs/disaster-recovery.md` - Plan completo
   - `procedimientos.md` - Runbook operacional

## Consideraciones de Costos

### Sin Costos (Free Tier):
- Replicación MongoDB Atlas
- Failover automático
- Backups

### Con Costos Potenciales:
- S3 Backups: ~$0.023/GB/mes
- Cross-region replication: ~$0.02/GB
- CloudWatch: ~$0.50/GB logs
- SNS: ~$0.50/millón notificaciones

**Total estimado**: $20-50/mes

## Métricas de Éxito

✓ RPO < 1 segundo (Replicación en tiempo real)
✓ RTO < 60 segundos (Failover automático)
✓ Recovery Rate: 100% (Todos los datos)
✓ Disponibilidad: 99.95%+ (Multi-región)

## Referencias

- [MongoDB Atlas Replica Set Documentation](https://docs.mongodb.com/atlas/reference/replica-set-configuration/)
- [MongoDB Backup Documentation](https://docs.mongodb.com/atlas/backup/)
- [AWS S3 Cross-Region Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [Terraform AWS Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [Plan completo](../docs/disaster-recovery.md)
