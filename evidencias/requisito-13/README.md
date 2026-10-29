# Requisito 13: 50 GB de Datos IoT

> Evidencia actual: proyección simulada tomando 0.4 GB como referencia indicada en la matriz. No significa que MongoDB contenga 50 GB; el reporte calcula el 0.8% y el factor estimado para escalar.

> Medición real ejecutada el 2026-10-21: MongoDB Atlas contiene 1,000 lecturas y 10 sensores (1,010 documentos), con aproximadamente 0.0003 GB de datos lógicos. El objetivo de 50 GB sigue pendiente; consulta `tamano_mongodb_real_20261021.txt`. La proyección simulada no reemplaza esta medición.

## Objetivo

Almacenar y gestionar un volumen significativo de datos IoT (≥50 GB) en MongoDB.

## Implementación

### Script Principal

**Archivo**: `scripts/generar_datos_iot.py`

Genera datos sintéticos realistas con:
- Múltiples sensores (100-10,000 configurable)
- Tipos de sensores diversos (weather, air_quality, energy, motion, etc.)
- Datos históricos (365 días)
- Insertión eficiente por lotes (1,000 docs/lote)
- Soporte para reanudación

### Modelo de Datos

Cada documento contiene:
```json
{
  "sensor_id": "sensor_XXXXXX",
  "timestamp": "2024-01-15T14:30:45Z",
  "tipo_sensor": "weather|air_quality|energy|motion|...",
  "temperatura": 15.0-35.0,
  "humedad": 30.0-90.0,
  "presion": 950.0-1050.0,
  "calidad_aire": 0-500,
  "energia": 0.0-1.0,
  "estado": "normal|warning|error|maintenance",
  "ubicacion": {
    "lat": -90.0-90.0,
    "lon": -180.0-180.0,
    "ciudad": "string",
    "pais": "string"
  },
  "confiabilidad": 0.8-1.0
}
```

**Tamaño aproximado por documento**: 2-5 KB

**Para 50 GB**: ~10-25 millones de documentos

## Proceso de Generación

### Fase 1: Instalación (5 minutos)

```powershell
# Activar entorno
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### Fase 2: Configuración (5 minutos)

```powershell
# Copiar y editar .env
Copy-Item .env.example .env
notepad .env

# Establecer MONGODB_URI con credenciales válidas
```

### Fase 3: Generación Incremental

#### Paso 1: Datos de Prueba (5 minutos)

```powershell
python scripts/generar_datos_iot.py `
  --num-sensors 100 `
  --total-documents 10000 `
  --batch-size 1000

# Resultado: ~20-50 MB
```

#### Paso 2: Escala Media (30 minutos)

```powershell
python scripts/generar_datos_iot.py `
  --num-sensors 500 `
  --total-documents 100000 `
  --batch-size 1000

# Resultado: ~200-500 MB
```

#### Paso 3: Escala Grande (1-2 horas)

```powershell
python scripts/generar_datos_iot.py `
  --num-sensors 2000 `
  --total-documents 1000000 `
  --batch-size 1000

# Resultado: ~2-5 GB
```

#### Paso 4: Escala Masiva (10-14 horas)

```powershell
# Ejecutar en segundo plano
python scripts/generar_datos_iot.py `
  --num-sensors 10000 `
  --total-documents 16000000 `
  --batch-size 1000 `
  --target-gb 50

# Resultado: ~50 GB
```

### Fase 4: Verificación

```powershell
# Verificar progreso en cualquier momento
python scripts/verificar_tamano_mongodb.py

# Debería mostrar:
# ✓ Cantidad de documentos
# ✓ Tamaño en GB
# ✓ Porcentaje de 50 GB
# ✓ Próximos pasos
```

## Índices de Base de Datos

Creados automáticamente por el script:

```javascript
db.sensor_readings.createIndex({ sensor_id: 1, timestamp: 1 })
db.sensor_readings.createIndex({ timestamp: 1 })
db.sensor_readings.createIndex({ tipo_sensor: 1 })
db.sensor_readings.createIndex({ sensor_id: 1 })
```

**Impacto en tamaño**: +15-20% (índices ocupan espacio adicional)

**Para 50 GB de datos**: ~7.5-10 GB de índices

## Resultados Esperados

### Estadísticas de 50 GB

```
📊 ESTADÍSTICAS GENERALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lecturas: 16,000,000+
Sensores: 10,000
Sensores Activos: 10,000
Sensores Inactivos: 0

📈 ALMACENAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Datos: 50.0 GB
Índices: 7.5 GB
Total: 57.5 GB
Objetivo: 50 GB
✓ OBJETIVO CUMPLIDO
```

### Desglose de Tamaño

| Componente | Tamaño | Porcentaje |
|-----------|--------|-----------|
| Documentos sensor_readings | 50.0 GB | 86.9% |
| Índices sensor_readings | 7.5 GB | 13.0% |
| Metadatos sensors | 10 MB | 0.02% |
| Total | 57.5 GB | 100% |

## Validación de Datos

### Verificación de Integridad

```powershell
# Ver estadísticas
python scripts/verificar_tamano_mongodb.py

# Salida esperada en evidencias/requisito-13/
```

### Consultas de Validación

```javascript
// En MongoDB Shell
use iot_platform

// Cantidad de documentos
db.sensor_readings.countDocuments()
// Resultado: 16,000,000+

// Rango de fechas
db.sensor_readings.aggregate([
  { $group: { _id: null, min: { $min: "$timestamp" }, max: { $max: "$timestamp" } } }
])
// Resultado: Rango de ~365 días

// Sensores únicos
db.sensor_readings.aggregate([
  { $group: { _id: "$sensor_id" } },
  { $count: "total" }
])
// Resultado: 10,000

// Distribución de tipos
db.sensor_readings.aggregate([
  { $group: { _id: "$tipo_sensor", count: { $sum: 1 } } }
])
// Resultado: Distribución uniforme entre tipos
```

## Monitoreo Continuo

### Script Automático (PowerShell)

```powershell
# Ejecutar cada 30 minutos
while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] Verificando progreso..."
    
    python scripts/verificar_tamano_mongodb.py | Tee-Object -FilePath "verificacion_$timestamp.log"
    
    Write-Host "Próxima verificación en 30 minutos..."
    Start-Sleep -Seconds 1800
}
```

## Problemas Comunes y Soluciones

### Generación se Detiene

**Síntoma**: Script se congela o se interrumpe

**Solución**:
```powershell
# El script soporta reanudación automática
# Simplemente vuelve a ejecutar el mismo comando
python scripts/generar_datos_iot.py --total-documents 16000000

# Continúa desde donde se quedó
```

### Memoria Insuficiente

**Síntoma**: "MemoryError" durante inserción

**Solución**:
```powershell
# Reducir tamaño de lote
python scripts/generar_datos_iot.py `
  --total-documents 16000000 `
  --batch-size 500  # Reducido de 1000

# O usar PowerShell con menos memoria
```

### Conexión a MongoDB Lenta

**Síntoma**: Inserciones muy lentas

**Solución**:
- Verificar ancho de banda de red
- Verificar latencia a MongoDB Atlas
- Considerar usar MongoDB local si es posible

## Cálculo de Tiempo Estimado

```
Documentos objetivo: 16,000,000
Tamaño por documento: 3 KB (promedio)
Documentos por lote: 1,000
Tiempo por lote: 2-5 segundos

Total de lotes: 16,000
Tiempo total: 16,000 × 3.5 segundos = 56,000 segundos ≈ 15.6 horas

Tiempo real estimado: 10-14 horas (con optimizaciones)
```

## Optimizaciones Aplicadas

1. **Bulk Insert**: Inserta en lotes de 1,000
2. **Sin load en RAM**: Generación streaming
3. **Reanudación**: Detecta documentos previos
4. **Índices Optimizados**: Creados antes de datos
5. **Batch Ordering**: Permite fallos parciales

## Evidencias a Capturar

1. ✓ Salida de `verificar_tamano_mongodb.py` mostrando ≥50 GB
2. ✓ Captura de dashboard mostrando progreso
3. ✓ Logs de generación con timestamps
4. ✓ Consultas de integridad de datos

## Archivos Generados

- `verificar_tamano_resultado.txt` - Salida de verificación
- `dashboard_iot_monitoreo.png` - Gráfico de progreso
- `logs_generacion.txt` - Logs de generación
- `query_validation.json` - Resultados de consultas

## Referencias

- Código: `scripts/generar_datos_iot.py`
- Verificación: `scripts/verificar_tamano_mongodb.py`
- Modelo: `docs/arquitectura.md` (Sección Escalabilidad)
- Dashboard: `dashboard/dashboard_monitoreo.py`
