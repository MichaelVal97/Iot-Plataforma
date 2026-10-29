# Catálogo de Datos IoT

Base de datos: `iot_platform`

catalogo del esquema de referencia; no requiere acceso a MongoDB

## Colección `sensor_readings`

Lecturas temporales generadas por sensores IoT.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `_id` | ObjectId | Sí | Identificador generado por MongoDB. |
| `sensor_id` | string | Sí | Identificador del sensor que produjo la lectura. |
| `timestamp` | datetime | Sí | Fecha y hora de la lectura. |
| `tipo_sensor` | string | Sí | Tipo de sensor, por ejemplo weather o temperature. |
| `temperatura` | number | Sí | Temperatura en grados Celsius. |
| `humedad` | number | Sí | Humedad relativa en porcentaje. |
| `presion` | number | Sí | Presión atmosférica en hPa. |
| `calidad_aire` | integer | Sí | Índice de calidad del aire (AQI). |
| `energia` | number | Sí | Lectura de energía en kW. |
| `estado` | string | Sí | Estado: normal, warning, error o maintenance. |
| `ubicacion.lat` | number | Sí | Latitud geográfica. |
| `ubicacion.lon` | number | Sí | Longitud geográfica. |
| `datos_adicionales.velocidad_viento` | number | Sí | Velocidad del viento simulada. |
| `datos_adicionales.radiacion_solar` | number | Sí | Radiación solar simulada. |
| `datos_adicionales.precipitacion` | number | Sí | Precipitación simulada. |
| `confiabilidad` | number | Sí | Confiabilidad estimada de la lectura, entre 0.8 y 1.0. |

## Colección `sensors`

Metadatos de los sensores registrados en la plataforma.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `_id` | ObjectId | Sí | Identificador generado por MongoDB. |
| `sensor_id` | string | Sí | Identificador único del sensor. |
| `tipo_sensor` | string | Sí | Categoría del sensor. |
| `ubicacion.lat` | number | Sí | Latitud geográfica. |
| `ubicacion.lon` | number | Sí | Longitud geográfica. |
| `ubicacion.ciudad` | string | Sí | Ciudad de instalación. |
| `ubicacion.pais` | string | Sí | País de instalación. |
| `estado` | string | Sí | Estado operativo del sensor; inicialmente activo. |
| `fecha_instalacion` | datetime | Sí | Fecha de instalación. |
| `fabricante` | string | Sí | Fabricante del sensor. |
| `modelo` | string | Sí | Modelo del sensor. |
| `ultima_calibracion` | datetime | Sí | Fecha de la última calibración. |
