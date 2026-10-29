# Resultado de consulta BigQuery

Consulta de solo lectura ejecutada el 22 de octubre de 2026 a las 02:04 UTC sobre el proyecto `iot-warehouse-512323`, dataset `iot_warehouse`.

```sql
SELECT 'dim_sensors' AS tabla, COUNT(*) AS filas
FROM `iot-warehouse-512323.iot_warehouse.dim_sensors`
UNION ALL
SELECT 'fact_readings', COUNT(*)
FROM `iot-warehouse-512323.iot_warehouse.fact_readings`;
```

Resultado observado:

| Tabla | Filas |
|---|---:|
| `dim_sensors` | 10 |
| `fact_readings` | 1.000 |

Los conteos coinciden con la carga ETL documentada. No se guardó captura de BigQuery Console; este archivo registra la salida obtenida mediante la consulta del cliente oficial de BigQuery.
