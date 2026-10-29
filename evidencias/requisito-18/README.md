# Evidencia - Data Warehouse en BigQuery

## Alcance

Esta evidencia documenta la carga ETL desde MongoDB Atlas hacia BigQuery para separar el almacenamiento operacional (OLTP) del analítico (OLAP).

- Proyecto: `iot-warehouse-512323`
- Dataset: `iot_warehouse`
- Tabla de dimensión: `dim_sensors`
- Tabla de hechos: `fact_readings`
- Script: `scripts/etl_mongodb_bigquery.py`

## Resultado observado de la carga

El 21 de octubre de 2026, la ejecución de `python scripts/etl_mongodb_bigquery.py --batch-size 1000` finalizó con código 0. El log reportó 10 sensores y 1.000 lecturas cargadas. La salida se conserva en `etl_bigquery_resultado.txt`.

## Verificación en BigQuery

El SQL de `verificar_bigquery.sql` se ejecutó en BigQuery el 22 de octubre de 2026 (UTC). La salida legible se conserva en `resultado_query.md`:

| Tabla | Filas observadas |
|---|---:|
| `dim_sensors` | 10 |
| `fact_readings` | 1.000 |

Pendiente únicamente: guardar una captura de BigQuery Console que muestre el SQL y su resultado, o exportar el resultado como CSV, en esta carpeta.

## Interpretación esperada

Los conteos observados coinciden con la carga ETL registrada. Son valores del momento de la consulta y pueden cambiar si se ejecuta otra carga.
