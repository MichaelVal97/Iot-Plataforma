# Requisito 15: Dashboard de Monitoreo

## Objetivo

Crear un dashboard visual en Python/Matplotlib que muestre estadísticas de IoT Platform.

## Implementación

### Script Principal

**Archivo**: `dashboard/dashboard_monitoreo.py`

**Tecnologías**:
- Python 3.7+
- Matplotlib 3.8+
- Pandas 2.1+
- PyMongo 4.6+

## Componentes del Dashboard

### 1. Estadísticas Generales (Texto)

```
ESTADÍSTICAS GENERALES
━━━━━━━━━━━━━━━━━━━━━━━━
Lecturas: 16,000,000
Sensores: 10,000
Sensores Activos: 10,000
Sensores Inactivos: 0

ALMACENAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━━
Datos: 50.0000 GB
Índices: 7.5000 GB
Total: 57.5000 GB
Objetivo: 50 GB
```

### 2. Distribución de Estados

**Tipo**: Gráfico de pastel

**Datos**:
- normal: 80%
- warning: 15%
- error: 4%
- maintenance: 1%

**Colores**:
- Verde: normal
- Amarillo: warning
- Rojo: error
- Naranja: maintenance

### 3. Sensores Activos vs Inactivos

**Tipo**: Gráfico de barras

**Datos**:
- Activos: Cantidad de sensores con lecturas
- Inactivos: Sensores sin lecturas recientes

### 4. Progreso hacia 50 GB

**Tipo**: Gráfico de barras horizontal

**Datos**:
- Eje X: Porcentaje (0-100%)
- Etiqueta: Porcentaje actual
- Color: Azul para progreso

### 5. Rangos de Temperatura

**Tipo**: Gráfico de barras agrupadas

**Datos**:
- Mínima
- Promedio
- Máxima

**Unidad**: °C (Celsius)

### 6. Rangos de Humedad

**Tipo**: Gráfico de barras agrupadas

**Datos**:
- Mínima
- Promedio
- Máxima

**Unidad**: % (Porcentaje)

### 7. Registros por Hora

**Tipo**: Gráfico de línea con marcadores

**Datos**:
- Eje X: Timestamp
- Eje Y: Cantidad de registros
- Rango: Últimas 100 horas (para claridad)

**Interpretación**: Muestra distribución temporal de datos

### 8. Temperatura a lo largo del Tiempo

**Tipo**: Gráfico de línea

**Datos**:
- Eje X: Timestamp
- Eje Y: Temperatura promedio (°C)
- Color: Rojo

### 9. Humedad a lo largo del Tiempo

**Tipo**: Gráfico de línea

**Datos**:
- Eje X: Timestamp
- Eje Y: Humedad promedio (%)
- Color: Azul

## Generación del Dashboard

### Ejecución Básica

```powershell
# Activar entorno
.\venv\Scripts\Activate.ps1

# Generar dashboard
python dashboard/dashboard_monitoreo.py

# Salida: dashboard/dashboard_iot_monitoreo.png
```

### Requisitos Previos

1. **Base de datos con datos**:
   ```powershell
   # Generar datos de prueba si no existen
   python scripts/generar_datos_iot.py --total-documents 10000
   ```

2. **Conexión a MongoDB configurada**:
   ```powershell
   # Verificar MONGODB_URI en .env
   cat .env | grep MONGODB_URI
   ```

3. **Matplotlib disponible**:
   ```powershell
   # Verificar
   python -c "import matplotlib; print(matplotlib.__version__)"
   ```

## Salida del Dashboard

### Características

- **Tamaño**: 1800×1400 píxeles
- **Resolución**: 150 DPI
- **Formato**: PNG
- **Ubicación**: `dashboard/dashboard_iot_monitoreo.png`

### Ejemplo de Estadísticas en Dashboard

```
Lecturas: 10,000,000
Sensores: 5,000
Tamaño: 25.5 GB / 50 GB (51.0%)

Temperatura: 24.3°C ± 5.2°C
Humedad: 60.1% ± 15.3%

Sensores Activos: 4,995 (99.9%)
Estados Normales: 95.2%
Última lectura: 2024-01-15 14:32:15
```

## Validación del Dashboard

### Verificación Visual

1. ✓ Aparecen 9 subplots
2. ✓ Todas las gráficas tienen datos
3. ✓ Ejes tienen etiquetas
4. ✓ Colores son distinguibles
5. ✓ Texto es legible
6. ✓ Sin mensajes de error

### Verificación Técnica

```powershell
# Verificar que la imagen se generó
Test-Path dashboard/dashboard_iot_monitoreo.png
# Resultado: True

# Obtener tamaño
Get-Item dashboard/dashboard_iot_monitoreo.png | Select-Object Length
# Resultado: 100KB+ (imagen con datos)
```

### Consultas de Validación

```javascript
// En MongoDB Shell, verificar que hay datos

// Cantidad mínima de documentos
db.sensor_readings.countDocuments() >= 1000
// Result: true

// Hay sensores
db.sensors.countDocuments() > 0
// Result: true

// Hay registros en diferentes días
db.sensor_readings.aggregate([
  { $group: { _id: { $dateToString: { format: "%Y-%m-%d", date: "$timestamp" } } } },
  { $count: "days" }
])
// Result: days >= 1
```

## Troubleshooting

### Dashboard No Se Genera

**Error**: "No data in sensor_readings"

**Solución**:
```powershell
# Generar datos primero
python scripts/generar_datos_iot.py --total-documents 1000

# Luego generar dashboard
python dashboard/dashboard_monitoreo.py
```

### Conexión a MongoDB Falla

**Error**: "Failed to connect to MongoDB"

**Solución**:
```powershell
# Verificar MONGODB_URI
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('MONGODB_URI')[:50])"

# Verificar conectividad
python scripts/verificar_tamano_mongodb.py
```

### Gráficos se Ven Vacíos

**Causa**: Datos insuficientes (< 1000 documentos)

**Solución**:
```powershell
# Generar más datos
python scripts/generar_datos_iot.py --total-documents 10000

# Reintentar dashboard
python dashboard/dashboard_monitoreo.py
```

## Mejoras Futuras

1. **Interactividad**: Usar Plotly/Dash para gráficos interactivos
2. **Actualización Automática**: Cronograma de generación diaria
3. **Alertas Visuales**: Cambios de color si datos están fuera de rango
4. **Exportación**: CSV, JSON, PDF además de PNG
5. **Multi-idioma**: Español/Inglés según configuración
6. **Temas**: Tema claro/oscuro seleccionable

## Archivos Generados

1. **dashboard_iot_monitoreo.png**: Imagen principal del dashboard
2. **dashboard_monitoreo_estadisticas.json**: Datos en JSON (futuro)
3. **dashboard_monitoreo.log**: Log de generación

## Consideraciones de Rendimiento

### Tiempo de Generación

- **Con 10K documentos**: 5-10 segundos
- **Con 1M documentos**: 15-30 segundos
- **Con 50GB (16M docs)**: 30-60 segundos

### Optimizaciones Aplicadas

1. Agregaciones con límite (últimas 100 horas)
2. Índices en MongoDB para consultas rápidas
3. Caché de conexión
4. Generación de gráficos eficiente

## Referencias

- Código: `dashboard/dashboard_monitoreo.py`
- Matplotlib docs: https://matplotlib.org/
- Pandas docs: https://pandas.pydata.org/
- PyMongo docs: https://pymongo.readthedocs.io/
