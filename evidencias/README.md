# Evidencias de Requisitos

Este directorio contiene evidencias de cumplimiento de cada requisito.

## Requisito 13: 50 GB de Datos IoT

**Descripción**: Proyección académica de escalamiento desde el volumen de referencia (~400 MB de la matriz). La evidencia simulada no afirma que existan 50 GB almacenados.

**Archivos esperados**:
- `requisito-13/verificar_tamano_resultado.txt` - Salida de verificación
- `requisito-13/tamano_mongodb_real_20261021.txt` - Medición real de Atlas (1,010 documentos; 0.0003 GB; objetivo de 50 GB pendiente)
- `requisito-13/README.md` - Explicación detallada

**Cómo verificar**:
```bash
python scripts/verificar_tamano_mongodb.py --demo --current-gb 0.4 --output evidencias/requisito-13/verificar_tamano_resultado.txt
```

## Requisito 14: Disaster Recovery Cross-Region

**Descripción**: Simulación local de replicación y failover entre una primaria y una réplica lógica. No aprovisiona AWS ni valida MongoDB Atlas.

**Evidencias generadas**:
- `requisito-14/verify_dr_resultado.txt` - Salida de validación
- `requisito-14/simulacion_dr.json` - Resultado con checksum, RPO y RTO local
- `requisito-14/README.md` - Alcance y procedimiento

**Cómo verificar**:
```bash
python scripts/verify_dr.py --demo
```

Esta evidencia comprueba recuperación de una copia local; no acredita replicación, backups ni failover reales en la nube.

## Requisito 15: Dashboard de Monitoreo

**Descripción**: Dashboard Python/Matplotlib con estadísticas de referencia en modo demo.

**Archivos esperados**:
- `requisito-15/dashboard_iot_monitoreo.png` - Imagen del dashboard simulado
- `requisito-15/estadisticas.json` - Datos extraídos
- `requisito-15/dashboard_mongodb_real_20261021.png` y `estadisticas_mongodb_real_20261021.json` - Dashboard y métricas reales de Atlas
- `requisito-15/README.md` - Descripción del dashboard

**Cómo generar**:
```bash
python dashboard/dashboard_monitoreo.py --demo --output evidencias/requisito-15/dashboard_iot_monitoreo.png
```

**Contenido del dashboard**:
- Cantidad total de sensores
- Cantidad total de registros
- Tamaño de la base de datos
- Tamaño de índices
- Temperatura promedio (min, promedio, max)
- Humedad promedio (min, promedio, max)
- Registros por intervalo de tiempo
- Sensores activos/inactivos
- Distribución de estados
- Última fecha de datos
- Porcentaje de cumplimiento de 50 GB

En modo demo, el tamaño y la serie temporal son métricas simuladas de referencia.

## Requisito 16: Infrastructure as Code (Terraform)

**Descripción**: Definir infraestructura AWS mediante Terraform.

**Evidencias**:
- `requisito-16/terraform_fmt.txt` - Resultado de `terraform fmt -check -recursive`
- `requisito-16/terraform_validate.txt` - Resultado de `terraform validate`
- `requisito-16/README.md` - Explicación de recursos

**Cómo verificar sin AWS** (inicializa el proveedor, valida configuración y no crea recursos):
```bash
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate
terraform -chdir=terraform fmt -check -recursive
```

**Recursos definidos en Terraform**:
- S3 buckets para backups (primaria + DR)
- Replicación S3 entre regiones
- DynamoDB table para rastreo
- CloudWatch logs y alarms
- SNS topics para alertas
- IAM roles y policies

No se ejecuta `terraform plan` ni `apply`: este proyecto simula DR localmente y no usa AWS ni requiere credenciales cloud. `terraform validate` comprueba la configuración HCL, no el acceso o disponibilidad de AWS.

## Requisito 17: Catálogo de Datos

**Descripción**: Generar un diccionario de campos de las colecciones IoT en formatos JSON y Markdown.

**Archivos generados**:
- `requisito-17/catalogo_datos.json`
- `requisito-17/catalogo_datos.md`

**Cómo generar**:
```powershell
python scripts/generar_catalogo_datos.py
```

## Requisito 18: Data Warehouse BigQuery

**Evidencias ejecutadas**:
- `requisito-18/etl_bigquery_resultado.txt` - Log de carga ETL: 10 sensores y 1,000 lecturas
- `requisito-18/verificar_bigquery.sql` - Consulta de conteos
- `requisito-18/resultado_query.md` - Resultado real de la consulta: 10 filas en `dim_sensors`, 1,000 en `fact_readings`
- `requisito-18/README.md` - Alcance y limitaciones

La evidencia confirma la carga y el conteo en BigQuery. No incluye captura de la consola web.

## Checklist de Validación

### Requisito 13 (50 GB)
- [x] Proyección calculada desde 0.4 GB de referencia
- [x] Reporte diferencia simulación de almacenamiento real
- [ ] Volumen real de MongoDB alcanza 50 GB

### Requisito 14 (DR)
- [x] Failover local simulado recupera registro replicado
- [x] Checksum coincidente y RPO simulado registrados
- [ ] Replicación y restauración reales en nube (fuera del alcance simulado)

### Requisito 15 (Dashboard)
- [ ] Dashboard se genera sin errores
- [ ] PNG contiene todos los gráficos
- [ ] Muestra datos realistas
- [ ] Incluye estadísticas de 50 GB
- [ ] Resolución mínima 1200x900

### Requisito 16 (Terraform)
- [ ] `terraform validate` OK
- [ ] `terraform fmt` OK
- [ ] `terraform plan` no tiene errores
- [ ] Archivo de plan guardado
- [ ] Documentación de recursos

## Datos Esperados

### Requisito 13
```
Total de documentos: 16,000,000+
Tamaño lógico: 50.0+ GB
Tamaño de índices: 7.5+ GB
Tamaño total: 57.5+ GB
Porcentaje: 100%+ ✓
```

### Requisito 14
```
Replicación Lag: < 1 segundo
Backup Last: Menos de 6 horas
Failover Time: 10-60 segundos
DR Region Status: OK
```

### Requisito 15
```
Sensores: 100-10,000
Registros: 1,000,000+
Temperatura promedio: 15-35°C
Humedad promedio: 30-90%
Estados normales: 80%+
```

### Requisito 16
```
Regiones: us-east-1, us-west-2
Recursos: 8+
Costo estimado: $0-50/mes
Estado: Ready to deploy
```

## Notas Importantes

1. **Escalabilidad**: La generación a 50 GB toma 10-14 horas
2. **Costos**: No se incurren costos hasta ejecutar `terraform apply`
3. **Validación Manual**: Algunos pasos requieren confirmación en consolas
4. **Documentación**: Cada requisito tiene guía en `docs/`

## Referencias

- Requisito 13: `docs/arquitectura.md` (Sección Escalabilidad)
- Requisito 14: `docs/disaster-recovery.md` (Completo)
- Requisito 15: `dashboard/dashboard_monitoreo.py` (Código)
- Requisito 16: `terraform/*.tf` (Código)
