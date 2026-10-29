# Database - MongoDB Setup

## Configuración de MongoDB Atlas

### Crear Cluster

1. Ir a [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crear o usar cuenta existente
3. Click "Create a cluster"
4. Configuración:
   - Tier: M0 Shared (gratuito)
   - Región primaria: N. Virginia (us-east-1)
   - Región secundaria: Oregon (us-west-2) - para DR

### Obtener Connection String

1. Click "Connect" en el cluster
2. Seleccionar "Drivers"
3. Seleccionar "Python 3.6 or later"
4. Copiar connection string
5. Reemplazar `<password>` con tu contraseña
6. Reemplazar `myFirstDatabase` con `iot_platform`

Ejemplo:
```
mongodb+srv://usuario:password@cluster0.mongodb.net/iot_platform?retryWrites=true&w=majority
```

### Configurar IP Whitelist

1. En Atlas, ir a "Network Access"
2. Click "Add IP Address"
3. Seleccionar "Allow access from anywhere" (para desarrollo)
   - O agregar tu IP específica
4. Click "Confirm"

## Colecciones

### sensor_readings

Contiene todas las lecturas de sensores.

```javascript
{
  "_id": ObjectId,
  "sensor_id": "sensor_000001",
  "timestamp": ISODate("2024-01-15T14:30:45.000Z"),
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
    "radiacion_solar": 450.0,
    "precipitacion": 0.0
  },
  "confiabilidad": 0.95
}
```

**Índices**:
```javascript
db.sensor_readings.createIndex({ sensor_id: 1, timestamp: 1 })
db.sensor_readings.createIndex({ timestamp: 1 })
db.sensor_readings.createIndex({ tipo_sensor: 1 })
db.sensor_readings.createIndex({ sensor_id: 1 })
```

### sensors

Metadatos de los sensores.

```javascript
{
  "_id": ObjectId,
  "sensor_id": "sensor_000001",
  "tipo_sensor": "weather",
  "ubicacion": {
    "lat": 40.7128,
    "lon": -74.0060,
    "ciudad": "Nueva York",
    "pais": "Estados Unidos"
  },
  "estado": "activo",
  "fecha_instalacion": ISODate("2023-06-15T00:00:00.000Z"),
  "fabricante": "SensorTech Inc",
  "modelo": "Model-5847",
  "ultima_calibracion": ISODate("2024-01-10T00:00:00.000Z")
}
```

**Índices**:
```javascript
db.sensors.createIndex({ sensor_id: 1 }, { unique: true })
db.sensors.createIndex({ tipo_sensor: 1 })
```

## Data Warehouse en BigQuery

MongoDB Atlas permanece como base operacional OLTP. Para análisis OLAP, `scripts/etl_mongodb_bigquery.py` copia los metadatos a `dim_sensors` y las mediciones a `fact_readings` en el dataset `iot_warehouse`. La relación entre ambas tablas es `sensor_id`; las coordenadas y medidas anidadas se aplanan durante la extracción.

La carga se realiza por lotes usando jobs de BigQuery y reemplaza las tablas en cada ejecución. Configura `BIGQUERY_PROJECT_ID`, `BIGQUERY_DATASET` y `BIGQUERY_LOCATION` en `.env`, autentícate mediante Application Default Credentials y ejecuta desde la raíz:

```powershell
python scripts/etl_mongodb_bigquery.py --batch-size 1000
```

Usa `--limit 100` para una prueba pequeña. La tabla de hechos conserva `reading_id` como identificador de origen y `sensor_id` como clave de relación.

## Consultas Comunes

```javascript
// Contar documentos
db.sensor_readings.countDocuments()

// Últimas lecturas
db.sensor_readings.find().sort({ timestamp: -1 }).limit(10)

// Lecturas por sensor
db.sensor_readings.find({ sensor_id: "sensor_000001" })

// Por rango de fechas
db.sensor_readings.find({
  timestamp: {
    $gte: ISODate("2024-01-01"),
    $lt: ISODate("2024-01-02")
  }
})

// Agregación: Temperatura promedio por día
db.sensor_readings.aggregate([
  {
    $group: {
      _id: {
        $dateToString: { format: "%Y-%m-%d", date: "$timestamp" }
      },
      avg_temp: { $avg: "$temperatura" },
      count: { $sum: 1 }
    }
  },
  { $sort: { _id: 1 } }
])
```

## Mantenimiento

### Backup Manual

```javascript
// En MongoDB Atlas Console:
// Deployment → Backup → Backup Now
```

### Estadísticas de Base de Datos

```javascript
db.stats()
db.sensor_readings.stats()
db.sensors.stats()
```

### Eliminar Datos (¡CUIDADO!)

```javascript
// Eliminar TODOS los documentos de sensor_readings
db.sensor_readings.deleteMany({})

// Eliminar sensor específico
db.sensor_readings.deleteMany({ sensor_id: "sensor_000001" })

// Eliminar BD completa
db.dropDatabase()
```

## Troubleshooting

### Conexión rechazada

- Verificar MONGODB_URI
- Verificar contraseña
- Verificar IP en whitelist
- Verificar red/firewall

### Demasiados archivos abiertos

- Aumentar límite: `ulimit -n 65536` (Unix/Mac)
- En Windows, reejecutar script

### Inserciones lentas

- Verificar tamaño de lote (1000 es bueno)
- Verificar índices
- Considerar background indexing

## Referencias

- [MongoDB Atlas Documentation](https://docs.mongodb.com/atlas/)
- [MongoDB Query Documentation](https://docs.mongodb.com/manual/query/)
- [MongoDB Indexes](https://docs.mongodb.com/manual/indexes/)
